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

from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from .analysis import run_case_analysis, run_chat_turn, run_document_draft
from .contexto import bloco_dos_documentos, texto_dos_relatos
from .docx_builder import DocxIndisponivel, build_docx, nome_do_arquivo
from .llm_providers import LLMError, provider_do_servidor
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


class ChatIn(BaseModel):
    user_id: str
    mensagem: str


class PecaIn(BaseModel):
    user_id: str
    modelo_id: str
    instrucoes: Optional[str] = None


def _erro(msg: str, status: int) -> JSONResponse:
    return JSONResponse({"erro": msg}, status_code=status)


def _resumo_do_caso(ctx: Dict[str, Any]) -> Dict[str, Any]:
    return {"titulo": ctx.get("titulo"), "cliente": ctx.get("cliente"), "area": ctx.get("area")}


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
        transcricao = texto_dos_relatos(ctx["relatos"])
        documentos_bloco, documentos_meta = bloco_dos_documentos(ctx["documentos"])
        if not transcricao and not documentos_bloco:
            return _erro("Registre o relato do caso antes de gerar a análise.", 404)
        anterior = await arm.ultima_analise(user_id, caso_id)
        informacoes: list[str] = []
        if body.incluir_chat:
            # Só o que o advogado escreveu: respostas da IA não viram fato do caso.
            mensagens = await arm.listar_mensagens(user_id, caso_id)
            informacoes = [m["conteudo"] for m in mensagens if m["papel"] == "user"][-MENSAGENS_NA_REANALISE:]
            if not informacoes:
                return _erro("Envie no chat as informações novas antes de atualizar a análise.", 400)
        try:
            provider = provider_do_servidor()
            analise = await run_in_threadpool(
                run_case_analysis, provider, transcricao, documentos_bloco, True,
                # Com fatos novos do chat a análise é refeita do zero: recebendo a versão anterior,
                # a IA tende a copiá-la e mantém teses que os fatos novos derrubaram. A versão
                # anterior continua salva no histórico.
                None if informacoes else (anterior["analise"] if anterior else None),
                informacoes or None)
        except LLMError as e:
            return _erro(str(e), 502)
        registro = await arm.salvar_analise(
            user_id, caso_id, analise, documentos_meta, f"{provider.name}:{provider.model}",
            origem="chat" if informacoes else "relato", mensagens_consideradas=len(informacoes))
        await marcar_analisado(user_id, caso_id, registro["versao"])
        return {"analise": para_analise_front(registro, caso_id)}

    @router.get("/analise/{caso_id}")
    async def obter_analises(caso_id: str, user_id: str = ""):
        arm, _ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        versoes = [para_analise_front(v, caso_id) for v in await arm.listar_analises(user_id.strip(), caso_id)]
        return {"analise": versoes[0] if versoes else None, "versoes": versoes}

    # ------------------------------------------------------------ chat
    @router.get("/chat/{caso_id}")
    async def listar_mensagens(caso_id: str, user_id: str = ""):
        arm, _ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        mensagens = await arm.listar_mensagens(user_id.strip(), caso_id)
        return {"mensagens": [mensagem_front(m) for m in mensagens]}

    @router.post("/chat/{caso_id}")
    async def enviar_mensagem(caso_id: str, body: ChatIn):
        user_id, mensagem = body.user_id.strip(), body.mensagem.strip()[:4000]
        arm, ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        if not mensagem:
            return _erro("Digite uma mensagem.", 400)
        ultima = await arm.ultima_analise(user_id, caso_id)
        relato = texto_dos_relatos(ctx["relatos"], LIMITE_RELATO_CHAT)
        if not ultima and not relato:
            return _erro("Registre o relato do caso antes de conversar com a IA.", 404)
        historico = await arm.listar_mensagens(user_id, caso_id, JANELA_CHAT)
        contexto = {"caso": _resumo_do_caso(ctx), "analise": ultima["analise"] if ultima else None,
                    "relato": relato}
        documentos_bloco, _meta = bloco_dos_documentos(ctx["documentos"])
        try:
            provider = provider_do_servidor()
            resposta = await run_in_threadpool(
                run_chat_turn, provider, contexto,
                [{"role": m["papel"], "content": m["conteudo"]} for m in historico],
                mensagem, documentos_bloco)
        except LLMError as e:
            return _erro(str(e), 502)
        novas = await arm.adicionar_mensagens(user_id, caso_id, [("user", mensagem), ("assistant", resposta)])
        return {"mensagens": [mensagem_front(m) for m in novas]}

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

    @router.get("/pecas/{caso_id}/{peca_id}/docx")
    async def baixar_peca(caso_id: str, peca_id: str, user_id: str = ""):
        arm, _ctx, erro = await _preparar(user_id, caso_id)
        if erro:
            return erro
        peca = await arm.obter_peca(user_id.strip(), caso_id, peca_id)
        if not peca:
            return _erro("Minuta não encontrada.", 404)
        try:
            conteudo = build_docx(peca["texto"])
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
        try:
            provider = provider_do_servidor()
            rascunho = await run_in_threadpool(run_document_draft, provider, contexto, modelo, instrucoes)
        except LLMError as e:
            return _erro(str(e), 502)
        if not rascunho.strip():
            return _erro("A IA não devolveu texto para a minuta. Tente novamente.", 502)
        peca = await arm.salvar_peca(user_id, caso_id, modelo, rascunho.strip(), instrucoes, ultima["versao"])
        return {"peca": peca_front(peca), "aviso": "Minuta gerada por IA — revise antes de protocolar."}

    return router
