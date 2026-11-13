"""
Rotas FastAPI da análise preliminar, do chat e das minutas. Montadas por `criar_router(...)`
no backend/main.py.

- O `user_id` vem do corpo/query SOMENTE porque quem chama é o servidor Next, que o lê do
  cookie assinado (mesma confiança das rotas /casos e /salvar-transcricao).
- Toda rota confere antes que o caso existe, é do usuário e não foi excluído; caso alheio
  responde 404, igual a caso inexistente.
- A chave da IA fica no servidor (env), nunca no navegador.
- O front manda só o que é novo (uma mensagem, um pedido de minuta); o histórico fica no
  banco e o backend lê dele o que precisa.

Os SDKs/HTTP de IA são bloqueantes: rodam em thread pool (run_in_threadpool).
"""
from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import APIRouter
from fastapi.concurrency import iterate_in_threadpool, run_in_threadpool
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from .analysis import run_case_analysis, run_chat_turn, run_chat_turn_stream, run_document_draft
from .areas import AREAS, area_front, normalizar_area
from .contexto import bloco_dos_documentos, fontes_para_salvar, material_para_analise, texto_dos_relatos
from .docx_builder import DocxIndisponivel, build_docx, nome_do_arquivo
from .minuta import texto_da_minuta
from .llm_providers import LLMError, provider_do_servidor
from .consumo import resumo_do_consumo
from .mapeador import mensagem_front, modelo_front, para_analise_front, peca_front
from .modelos_pecas import FASES, GRUPOS, MODELOS, obter_modelo
from .storage import Armazenamento

# (user_id, caso_id) -> {"titulo", "cliente", "area", "relatos": [...], "documentos": [...]}
# ou None quando o caso não existe para esse usuário (ou foi excluído).
ObterContexto = Callable[[str, str], Awaitable[Optional[Dict[str, Any]]]]
MarcarAnalisado = Callable[[str, str, int], Awaitable[None]]

# Limite do Groq no plano gratuito: 8 mil tokens por minuto. O contexto do chat e da minuta
# precisa caber nisso com folga; a análise já resume o relato.
JANELA_CHAT = 10  # mensagens anteriores enviadas à IA a cada pergunta
MENSAGENS_NA_REANALISE = 20  # últimas mensagens do advogado consideradas ao atualizar a análise
LIMITE_RELATO_CHAT = 6_000


class AnaliseIn(BaseModel):
    user_id: str
    # Reanálise com o que o advogado contou no chat (botão "Atualizar análise com a conversa").
    incluir_chat: bool = False
    fonte_tipo: Optional[str] = None
    fonte_id: Optional[str] = None


class ChatIn(BaseModel):
    user_id: str
    mensagem: str


class PecaIn(BaseModel):
    user_id: str
    modelo_id: str
    instrucoes: Optional[str] = None


def _erro(msg: str, status: int) -> JSONResponse:
    return JSONResponse({"erro": msg}, status_code=status)


def _evento(dados: Dict[str, Any]) -> str:
    """Uma linha do stream NDJSON do chat."""
    return json.dumps(dados, ensure_ascii=False) + "\n"


def _resumo_do_caso(ctx: Dict[str, Any]) -> Dict[str, Any]:
    return {"titulo": ctx.get("titulo"), "cliente": ctx.get("cliente"), "area": ctx.get("area")}


def _area_do_caso(ctx: Dict[str, Any]) -> Optional[str]:
    """Área do catálogo que escolhe a orientação do prompt; None = prompt genérico."""
    return normalizar_area(ctx.get("area"))


async def _registrar(arm, user_id: str, caso_id: str, tarefa: str, provider) -> None:
    """Grava os tokens da chamada, inclusive as que falharam no meio (também são cobradas)."""
    if provider is None:
        return
    try:
        await arm.registrar_consumo(user_id, caso_id, tarefa, provider.name, provider.model,
                                    provider.tirar_consumo())
    except Exception:  # noqa: BLE001 — medir custo nunca pode derrubar a resposta ao usuário
        pass


def criar_router(obter_contexto: ObterContexto,
                 armazenamento: Callable[[], Optional[Armazenamento]],
                 marcar_analisado: MarcarAnalisado) -> APIRouter:
    router = APIRouter(tags=["analise"])

    async def _preparar(user_id: str, caso_id: str):
        """(armazenamento, contexto) ou a resposta de erro pronta."""
        user_id, caso_id = user_id.strip(), caso_id.strip()
        if not user_id or not caso_id:
            return None, None, _erro("Informe o usuário e o caso.", 400)
        arm = armazenamento()
        if arm is None:
            return None, None, _erro("MongoDB não configurado.", 503)
        ctx = await obter_contexto(user_id, caso_id)
        if ctx is None:
            return None, None, _erro("Caso não encontrado.", 404)
        return arm, ctx, None

    # ------------------------------------------------------------ análise
    @router.post("/analise/{caso_id}")
    async def solicitar_analise(caso_id: str, body: AnaliseIn):
        user_id = body.user_id.strip()
        arm, ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        anterior = await arm.ultima_analise(user_id, caso_id)
        informacoes: list[str] = []
        if body.incluir_chat:
            # Só o que o advogado escreveu: respostas da IA não viram fato do caso.
            mensagens = await arm.listar_mensagens(user_id, caso_id)
            informacoes = [m["conteudo"] for m in mensagens if m["papel"] == "user"][-MENSAGENS_NA_REANALISE:]
            if not informacoes:
                return _erro("Envie no chat as informações novas antes de atualizar a análise.", 400)
        transcricao, documentos_bloco, documentos_meta = material_para_analise(
            ctx["relatos"], ctx["documentos"],
            ja_existe_analise=anterior is not None,
            incluir_chat=bool(informacoes),
            fonte_tipo=body.fonte_tipo, fonte_id=body.fonte_id)
        if not transcricao and not documentos_bloco:
            return _erro("Registre o relato do caso antes de gerar a análise.", 404)
        area = _area_do_caso(ctx)
        provider = None
        try:
            provider = provider_do_servidor()
            # Chat ou relato novo: refaz os cards. Com a análise anterior no prompt a IA
            # copia o resumo velho (“faltam dados”) e a tela não muda.
            # Arquivo novo: aí sim manda a anterior, para incorporar só o PDF.
            tipo = (body.fonte_tipo or "").strip().lower()
            usar_anterior = (
                anterior
                and not informacoes
                and tipo == "documento"
            )
            analise = await run_in_threadpool(
                run_case_analysis, provider, transcricao, documentos_bloco, True,
                anterior["analise"] if usar_anterior else None,
                informacoes or None, area)
        except LLMError as e:
            return _erro(str(e), 502)
        finally:
            await _registrar(arm, user_id, caso_id, "atualizar_analise_chat" if informacoes else "analise",
                             provider)
        fontes = fontes_para_salvar(
            ctx["documentos"], anterior,
            incluir_chat=bool(informacoes), fonte_tipo=body.fonte_tipo, fonte_id=body.fonte_id)
        registro = await arm.salvar_analise(
            user_id, caso_id, analise, documentos_meta, f"{provider.name}:{provider.model}",
            origem="chat" if informacoes else "relato", mensagens_consideradas=len(informacoes),
            fonte_tipo=fontes["fonte_tipo"], fonte_id=fontes["fonte_id"],
            fonte_nome=fontes["fonte_nome"], fontes_ids=fontes["fontes_ids"], area=area)
        await marcar_analisado(user_id, caso_id, registro["versao"])
        registros = await arm.listar_analises(user_id, caso_id)
        analises = [para_analise_front(item, caso_id) for item in reversed(registros)]
        versoes = [para_analise_front(item, caso_id) for item in registros]
        return {
            "analise": para_analise_front(registro, caso_id),
            "analises": analises,
            "versoes": versoes,
        }

    @router.get("/analise/{caso_id}")
    async def obter_analises(caso_id: str, user_id: str = ""):
        arm, _ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        registros = await arm.listar_analises(user_id.strip(), caso_id)
        analises = [para_analise_front(item, caso_id) for item in reversed(registros)]
        versoes = [para_analise_front(item, caso_id) for item in registros]
        return {
            "analise": analises[-1] if analises else None,
            "analises": analises,
            "versoes": versoes,
        }

    # ------------------------------------------------------------ chat
    @router.get("/chat/{caso_id}")
    async def listar_mensagens(caso_id: str, user_id: str = ""):
        arm, _ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        mensagens = await arm.listar_mensagens(user_id.strip(), caso_id)
        return {"mensagens": [mensagem_front(m) for m in mensagens]}

    async def _turno_do_chat(caso_id: str, body: ChatIn):
        """((arm, user_id, mensagem, argumentos do turno), None) ou (None, resposta de erro)."""
        user_id, mensagem = body.user_id.strip(), body.mensagem.strip()[:4000]
        arm, ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return None, erro
        if not mensagem:
            return None, _erro("Digite uma mensagem.", 400)
        ultima = await arm.ultima_analise(user_id, caso_id)
        relato = texto_dos_relatos(ctx["relatos"], LIMITE_RELATO_CHAT)
        if not ultima and not relato:
            return None, _erro("Registre o relato do caso antes de conversar com a IA.", 404)
        historico = await arm.listar_mensagens(user_id, caso_id, JANELA_CHAT)
        contexto = {"caso": _resumo_do_caso(ctx), "analise": ultima["analise"] if ultima else None,
                    "relato": relato}
        documentos_bloco, _meta = bloco_dos_documentos(ctx["documentos"])
        argumentos = dict(
            case_context_json=contexto,
            conversation_history=[{"role": m["papel"], "content": m["conteudo"]} for m in historico],
            new_message=mensagem, documentos_bloco=documentos_bloco, area=_area_do_caso(ctx))
        return (arm, user_id, mensagem, argumentos), None

    @router.post("/chat/{caso_id}")
    async def enviar_mensagem(caso_id: str, body: ChatIn):
        turno, erro = await _turno_do_chat(caso_id, body)
        if erro:
            return erro
        arm, user_id, mensagem, argumentos = turno
        provider = None
        try:
            provider = provider_do_servidor()
            resposta = await run_in_threadpool(lambda: run_chat_turn(provider, **argumentos))
        except LLMError as e:
            return _erro(str(e), 502)
        finally:
            await _registrar(arm, user_id, caso_id, "chat", provider)
        novas = await arm.adicionar_mensagens(user_id, caso_id, [("user", mensagem), ("assistant", resposta)])
        return {"mensagens": [mensagem_front(m) for m in novas]}

    @router.post("/chat/{caso_id}/stream")
    async def enviar_mensagem_ao_vivo(caso_id: str, body: ChatIn):
        """
        Mesma conversa de POST /chat, mas a resposta chega enquanto a IA escreve. Uma linha JSON por
        evento (NDJSON): {"tipo": "trecho", "texto"} várias vezes, depois {"tipo": "fim", "mensagens"}
        com as duas mensagens já gravadas, ou {"tipo": "erro", "erro"}. Só grava se a resposta terminar.
        """
        turno, erro = await _turno_do_chat(caso_id, body)
        if erro:
            return erro
        arm, user_id, mensagem, argumentos = turno
        try:
            provider = provider_do_servidor()
        except LLMError as e:
            return _erro(str(e), 502)

        async def eventos():
            partes = []
            try:
                async for trecho in iterate_in_threadpool(run_chat_turn_stream(provider, **argumentos)):
                    partes.append(trecho)
                    yield _evento({"tipo": "trecho", "texto": trecho})
                resposta = "".join(partes).strip()
                if not resposta:
                    raise LLMError("A IA não respondeu. Tente de novo.")
                novas = await arm.adicionar_mensagens(
                    user_id, caso_id, [("user", mensagem), ("assistant", resposta)])
                yield _evento({"tipo": "fim", "mensagens": [mensagem_front(m) for m in novas]})
            except LLMError as e:
                yield _evento({"tipo": "erro", "erro": str(e)})
            except Exception:  # noqa: BLE001 — o stream já começou: o erro vai como evento, não como 500
                yield _evento({"tipo": "erro", "erro": "Não foi possível concluir a resposta. Tente de novo."})
            finally:
                await _registrar(arm, user_id, caso_id, "chat", provider)

        return StreamingResponse(eventos(), media_type="application/x-ndjson",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    # ------------------------------------------------------------ áreas
    @router.get("/areas")
    async def listar_areas():
        """Áreas jurídicas aceitas em `legal_area`; cada uma tem orientação própria na IA.
        `gruposPecas` = grupos de /pecas/modelos que fazem sentido para a área."""
        return {"areas": [area_front(a) for a in AREAS]}

    # ------------------------------------------------------------ consumo
    @router.get("/consumo/{caso_id}")
    async def consumo_do_caso(caso_id: str, user_id: str = ""):
        """Tokens gastos no caso, por tarefa, e o custo estimado (SOPHIA_PRECO_IA_USD)."""
        arm, _ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        return resumo_do_consumo(await arm.listar_consumo(user_id.strip(), caso_id))

    # ------------------------------------------------------------ peças
    @router.get("/pecas/modelos")
    async def listar_modelos():
        return {"modelos": [modelo_front(m) for m in MODELOS], "grupos": GRUPOS, "fases": FASES}

    @router.get("/pecas/{caso_id}")
    async def listar_pecas(caso_id: str, user_id: str = ""):
        arm, _ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        pecas = await arm.listar_pecas(user_id.strip(), caso_id)
        return {"pecas": [peca_front(p, com_texto=False) for p in pecas]}

    @router.get("/pecas/{caso_id}/{peca_id}")
    async def obter_peca(caso_id: str, peca_id: str, user_id: str = ""):
        arm, _ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        peca = await arm.obter_peca(user_id.strip(), caso_id, peca_id)
        if not peca:
            return _erro("Minuta não encontrada.", 404)
        return {"peca": peca_front(peca)}

    @router.delete("/pecas/{caso_id}/{peca_id}")
    async def excluir_peca(caso_id: str, peca_id: str, user_id: str = ""):
        arm, _ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        if not await arm.excluir_peca(user_id.strip(), caso_id, peca_id):
            return _erro("Minuta não encontrada.", 404)
        return {"ok": True}

    @router.get("/pecas/{caso_id}/{peca_id}/docx")
    async def baixar_peca(caso_id: str, peca_id: str, user_id: str = ""):
        arm, _ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        peca = await arm.obter_peca(user_id.strip(), caso_id, peca_id)
        if not peca:
            return _erro("Minuta não encontrada.", 404)
        try:
            conteudo = build_docx(peca["texto"], peca.get("estrutura"))
        except DocxIndisponivel as e:
            return _erro(str(e), 503)
        return Response(
            content=conteudo,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{nome_do_arquivo(peca["titulo"])}"'})

    @router.post("/pecas/{caso_id}")
    async def gerar_peca(caso_id: str, body: PecaIn):
        user_id = body.user_id.strip()
        arm, ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        modelo = obter_modelo(body.modelo_id)
        if not modelo:
            return _erro("Escolha um modelo de peça válido.", 400)
        ultima = await arm.ultima_analise(user_id, caso_id)
        if not ultima:
            return _erro("Gere a análise preliminar do caso antes de pedir uma minuta.", 409)
        instrucoes = (body.instrucoes or "").strip()[:2000] or None
        contexto = {"caso": _resumo_do_caso(ctx), "analise": ultima["analise"],
                    "relato": texto_dos_relatos(ctx["relatos"], LIMITE_RELATO_CHAT)}
        provider = None
        try:
            provider = provider_do_servidor()
            estrutura = await run_in_threadpool(run_document_draft, provider, contexto, modelo, instrucoes,
                                               area=_area_do_caso(ctx))
        except LLMError as e:
            return _erro(str(e), 502)
        finally:
            await _registrar(arm, user_id, caso_id, "peca", provider)
        peca = await arm.salvar_peca(user_id, caso_id, modelo, texto_da_minuta(estrutura), instrucoes,
                                     ultima["versao"], estrutura)
        return {"peca": peca_front(peca), "aviso": "Minuta gerada por IA — revise antes de protocolar."}

    return router
