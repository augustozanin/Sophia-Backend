"""
Rotas do acompanhamento de prazos. Montadas por `criar_router(...)` no backend/main.py.

O `user_id` vem do corpo/query SOMENTE porque quem chama é o servidor Next, que o lê do
cookie assinado (mesma confiança das demais rotas). Item de outro usuário responde 404.

A Sophia NÃO calcula o prazo: ela traz a intimação do DJEN e o advogado define a data
final. O que o backend guarda é a data que ele escolheu.

Sincronização sob demanda (a tela pede ao abrir e no botão "Atualizar agora"): o backend
roda como função serverless, sem processo em segundo plano. Uma rotina agendada pode chamar
a mesma função `sincronizar_usuario` no futuro.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from . import djen
from .numeros import formatar_processo, normalizar_oab, normalizar_processo
from .storage import ArmazenamentoPrazos, oid

FUSO = timezone(timedelta(hours=-3))
MAX_MONITORAMENTOS = 20
DIAS_INICIAIS_OAB = 30          # primeira consulta por OAB: últimos 30 dias
SOBREPOSICAO_DIAS = 5           # as consultas seguintes repetem alguns dias, por segurança
DIAS_A_FRENTE = 7               # o DJEN registra a comunicação antes do dia da disponibilização
MAX_PAGINAS = 10                # 1.000 intimações por consulta
INTERVALO_AUTOMATICO = timedelta(minutes=30)
INTERVALO_MINIMO = timedelta(minutes=1)
DIAS_PUBLICACOES_TRATADAS = 90  # tratadas aparecem por 90 dias; pendentes, sempre
RESUMO_TEXTO = 1_200            # caracteres do teor que vão no painel

# (user_id, caso_id) -> o caso existe, é do usuário e não foi excluído
CasoDoUsuario = Callable[[str, str], Awaitable[bool]]


def agora() -> datetime:
    return datetime.now(FUSO).replace(microsecond=0, tzinfo=None)


def agora_iso() -> str:
    return agora().strftime("%Y-%m-%dT%H:%M:%S")


def _erro(msg: str, status: int) -> JSONResponse:
    return JSONResponse({"erro": msg}, status_code=status)


def _data_valida(valor: object) -> Optional[str]:
    texto = str(valor or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
        return None
    try:
        date.fromisoformat(texto)
    except ValueError:
        return None
    return texto


# ---------------------------------------------------------------- formato do front
def monitoramento_front(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "tipo": doc["tipo"],
        "oabNumero": doc.get("oab_numero"),
        "oabUf": doc.get("oab_uf"),
        "numeroProcesso": doc.get("numero_processo"),
        "casoId": doc.get("caso_id"),
        "criadoEm": doc.get("criado_em"),
        "ultimaSincronizacao": doc.get("ultima_sincronizacao"),
        "ultimoErro": doc.get("ultimo_erro"),
    }


def publicacao_front(doc: Dict[str, Any], completo: bool = False) -> Dict[str, Any]:
    """No painel o teor vem resumido (há intimações de 20 mil caracteres e o painel lista até
    300); o inteiro teor sai em GET /prazos/publicacoes/{id}."""
    texto = doc.get("texto") or ""
    truncado = not completo and len(texto) > RESUMO_TEXTO
    return {
        "id": str(doc["_id"]),
        "djenId": doc.get("djen_id"),
        "dataDisponibilizacao": doc.get("data_disponibilizacao"),
        "tribunal": doc.get("tribunal") or "",
        "orgao": doc.get("orgao") or "",
        "tipoComunicacao": doc.get("tipo_comunicacao") or "",
        "tipoDocumento": doc.get("tipo_documento") or "",
        "classe": doc.get("classe") or "",
        "numeroProcesso": doc.get("numero_processo") or "",
        "texto": texto[:RESUMO_TEXTO].rstrip() if truncado else texto,
        "textoTruncado": truncado,
        "link": doc.get("link"),
        "advogados": doc.get("advogados") or [],
        "partes": doc.get("partes") or [],
        "situacao": doc.get("situacao") or "pendente",
        "cancelada": bool(doc.get("cancelada")),
        "motivoCancelamento": doc.get("motivo_cancelamento"),
        "capturadaEm": doc.get("capturada_em"),
    }


def prazo_front(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "publicacaoId": doc.get("publicacao_id"),
        "casoId": doc.get("caso_id"),
        "numeroProcesso": doc.get("numero_processo"),
        "descricao": doc.get("descricao") or "",
        "dataFinal": doc.get("data_final"),
        "cumprido": bool(doc.get("cumprido")),
        "cumpridoEm": doc.get("cumprido_em"),
        "criadoEm": doc.get("criado_em"),
    }


# ---------------------------------------------------------------- sincronização
def _ultimo_contato(mon: Dict[str, Any]) -> Optional[datetime]:
    datas = [mon.get("ultima_sincronizacao"), mon.get("ultima_tentativa")]
    validas = []
    for valor in datas:
        try:
            validas.append(datetime.fromisoformat(str(valor)))
        except (TypeError, ValueError):
            continue
    return max(validas) if validas else None


def filtros_da_consulta(mon: Dict[str, Any], hoje: date) -> Dict[str, str]:
    if mon["tipo"] == "oab":
        filtros = {"numeroOab": mon["oab_numero"], "ufOab": mon["oab_uf"]}
    else:
        filtros = {"numeroProcesso": mon["numero_processo"]}
    ate = _data_valida(mon.get("sincronizado_ate"))
    if ate:
        inicio: Optional[date] = date.fromisoformat(ate) - timedelta(days=SOBREPOSICAO_DIAS)
    elif mon["tipo"] == "oab":
        inicio = hoje - timedelta(days=DIAS_INICIAIS_OAB)
    else:
        inicio = None  # processo novo: o histórico inteiro dele no DJEN
    if inicio:
        filtros["dataDisponibilizacaoInicio"] = inicio.isoformat()
        filtros["dataDisponibilizacaoFim"] = (hoje + timedelta(days=DIAS_A_FRENTE)).isoformat()
    return filtros


async def sincronizar_monitoramento(arm: ArmazenamentoPrazos, buscar: djen.Buscar, mon: Dict[str, Any]) -> int:
    """Consulta o DJEN para um monitoramento e grava o que chegou. Devolve quantas intimações são novas."""
    momento = agora()
    filtros = filtros_da_consulta(mon, momento.date())
    try:
        itens = await djen.buscar_comunicacoes(buscar, filtros, MAX_PAGINAS)
    except djen.ErroDjen as exc:
        await arm.atualizar_monitoramento(mon["user_id"], mon["_id"], {
            "ultimo_erro": str(exc),
            # Limite do DJEN não conta como tentativa: a próxima abertura da tela tenta de novo.
            **({} if exc.limite else {"ultima_tentativa": momento.isoformat()}),
        })
        raise
    normalizados = [n for n in (djen.normalizar(item) for item in itens) if n]
    novas = await arm.salvar_publicacoes(mon["user_id"], str(mon["_id"]), normalizados, momento.isoformat())
    await arm.atualizar_monitoramento(mon["user_id"], mon["_id"], {
        "ultima_sincronizacao": momento.isoformat(),
        "sincronizado_ate": momento.date().isoformat(),
        "ultimo_erro": None,
    })
    return novas


async def sincronizar_usuario(arm: ArmazenamentoPrazos, buscar: djen.Buscar, user_id: str,
                              forcar: bool = False, caso_id: Optional[str] = None) -> Dict[str, Any]:
    """Sincroniza os monitoramentos vencidos (todos, com `forcar`), um por vez.
    Um 429 do DJEN para tudo: insistir só prolonga o bloqueio."""
    intervalo = INTERVALO_MINIMO if forcar else INTERVALO_AUTOMATICO
    momento = agora()
    novas, erros, consultados = 0, [], 0
    for mon in await arm.listar_monitoramentos(user_id, caso_id):
        ultimo = _ultimo_contato(mon)
        if ultimo and momento - ultimo < intervalo:
            continue
        consultados += 1
        try:
            novas += await sincronizar_monitoramento(arm, buscar, mon)
        except djen.ErroDjen as exc:
            erros.append(str(exc))
            if exc.limite:
                break
    return {"novas": novas, "consultados": consultados, "erros": list(dict.fromkeys(erros))}


# ---------------------------------------------------------------- corpo das rotas
class NovoMonitoramentoIn(BaseModel):
    user_id: str
    tipo: str
    oab_numero: Optional[str] = None
    oab_uf: Optional[str] = None
    numero_processo: Optional[str] = None
    caso_id: Optional[str] = None


class VinculoIn(BaseModel):
    user_id: str
    caso_id: Optional[str] = None


class SincronizarIn(BaseModel):
    user_id: str
    forcar: bool = False
    caso_id: Optional[str] = None


class SituacaoIn(BaseModel):
    user_id: str
    situacao: str


class NovoPrazoIn(BaseModel):
    user_id: str
    descricao: str
    data_final: str
    publicacao_id: Optional[str] = None
    caso_id: Optional[str] = None
    numero_processo: Optional[str] = None


class AlteraPrazoIn(BaseModel):
    user_id: str
    descricao: Optional[str] = None
    data_final: Optional[str] = None
    cumprido: Optional[bool] = None


def criar_router(armazenamento: Callable[[], Optional[ArmazenamentoPrazos]],
                 caso_do_usuario: CasoDoUsuario,
                 buscar: djen.Buscar = djen.buscar_http) -> APIRouter:
    router = APIRouter(prefix="/prazos", tags=["prazos"])

    def _preparar(user_id: str):
        if not user_id.strip():
            return None, _erro("Informe o usuário.", 400)
        arm = armazenamento()
        if arm is None:
            return None, _erro("MongoDB não configurado.", 503)
        return arm, None

    async def _painel(arm: ArmazenamentoPrazos, user_id: str, caso_id: Optional[str]) -> Dict[str, Any]:
        monitoramentos = await arm.listar_monitoramentos(user_id, caso_id)
        desde = (agora().date() - timedelta(days=DIAS_PUBLICACOES_TRATADAS)).isoformat()
        if caso_id:
            processos = [m["numero_processo"] for m in monitoramentos if m["tipo"] == "processo"]
            publicacoes = await arm.listar_publicacoes(user_id, processos, desde) if processos else []
            prazos = await arm.listar_prazos(user_id, caso_id, processos)
        else:
            publicacoes = await arm.listar_publicacoes(user_id, None, desde)
            prazos = await arm.listar_prazos(user_id)
        return {
            "monitoramentos": [monitoramento_front(m) for m in monitoramentos],
            "publicacoes": [publicacao_front(p) for p in publicacoes],
            "prazos": [prazo_front(p) for p in prazos],
        }

    async def _caso_valido(user_id: str, caso_id: Optional[str]):
        """(caso_id limpo ou None, erro)."""
        caso_id = (caso_id or "").strip() or None
        if caso_id and not await caso_do_usuario(user_id, caso_id):
            return None, _erro("Caso não encontrado.", 404)
        return caso_id, None

    # ------------------------------------------------------------ painel
    @router.get("/painel")
    async def obter_painel(user_id: str = "", caso_id: str = ""):
        user_id = user_id.strip()
        arm, erro = _preparar(user_id)
        if erro:
            return erro
        caso, erro = await _caso_valido(user_id, caso_id)
        if erro:
            return erro
        return await _painel(arm, user_id, caso)

    @router.post("/sincronizar")
    async def sincronizar(body: SincronizarIn):
        user_id = body.user_id.strip()
        arm, erro = _preparar(user_id)
        if erro:
            return erro
        caso, erro = await _caso_valido(user_id, body.caso_id)
        if erro:
            return erro
        resumo = await sincronizar_usuario(arm, buscar, user_id, body.forcar, caso)
        return {**resumo, "painel": await _painel(arm, user_id, caso)}

    # ------------------------------------------------------------ monitoramentos
    @router.post("/monitoramentos")
    async def criar_monitoramento(body: NovoMonitoramentoIn):
        user_id = body.user_id.strip()
        arm, erro = _preparar(user_id)
        if erro:
            return erro
        caso, erro = await _caso_valido(user_id, body.caso_id)
        if erro:
            return erro

        if body.tipo == "oab":
            if caso:
                return _erro("No caso, acompanhe pelo número do processo.", 400)
            numero, uf, problema = normalizar_oab(body.oab_numero, body.oab_uf)
            if problema:
                return _erro(problema, 400)
            chave = f"oab:{numero}/{uf}"
            campos = {"tipo": "oab", "oab_numero": numero, "oab_uf": uf, "numero_processo": None, "caso_id": None}
        elif body.tipo == "processo":
            numero, problema = normalizar_processo(body.numero_processo)
            if problema:
                return _erro(problema, 400)
            chave = f"processo:{numero}"
            campos = {"tipo": "processo", "oab_numero": None, "oab_uf": None, "numero_processo": numero,
                      "caso_id": caso}
        else:
            return _erro("Escolha acompanhar por OAB ou por número do processo.", 400)

        existente = await arm.monitoramento_por_chave(user_id, chave)
        if existente:
            if caso and existente.get("caso_id") and existente["caso_id"] != caso:
                return _erro(f"O processo {formatar_processo(numero)} já está ligado a outro caso.", 409)
            if caso and not existente.get("caso_id"):
                await arm.atualizar_monitoramento(user_id, existente["_id"], {"caso_id": caso})
            monitoramento = await arm.monitoramento_por_chave(user_id, chave)
        else:
            if await arm.contar_monitoramentos(user_id) >= MAX_MONITORAMENTOS:
                return _erro(f"Limite de {MAX_MONITORAMENTOS} acompanhamentos por conta. Remova um para incluir outro.", 409)
            monitoramento = await arm.criar_monitoramento({
                **campos, "user_id": user_id, "chave": chave, "criado_em": agora_iso(),
                "ultima_sincronizacao": None, "sincronizado_ate": None, "ultimo_erro": None,
            })

        # Primeira consulta na hora, para a tela já mostrar o que existe.
        aviso = None
        if not monitoramento.get("ultima_sincronizacao"):
            try:
                await sincronizar_monitoramento(arm, buscar, monitoramento)
            except djen.ErroDjen as exc:
                aviso = str(exc)
        return {"aviso": aviso, "painel": await _painel(arm, user_id, caso)}

    @router.patch("/monitoramentos/{monitoramento_id}")
    async def vincular_caso(monitoramento_id: str, body: VinculoIn):
        """Liga (ou desliga, com caso_id vazio) um processo acompanhado a um caso."""
        user_id = body.user_id.strip()
        arm, erro = _preparar(user_id)
        if erro:
            return erro
        mon = await arm.obter_monitoramento(user_id, monitoramento_id)
        if not mon:
            return _erro("Acompanhamento não encontrado.", 404)
        if mon["tipo"] != "processo":
            return _erro("Só um processo pode ser ligado a um caso.", 400)
        caso, erro = await _caso_valido(user_id, body.caso_id)
        if erro:
            return erro
        await arm.atualizar_monitoramento(user_id, mon["_id"], {"caso_id": caso})
        return {"monitoramento": monitoramento_front({**mon, "caso_id": caso})}

    @router.delete("/monitoramentos/{monitoramento_id}")
    async def remover_monitoramento(monitoramento_id: str, user_id: str = ""):
        user_id = user_id.strip()
        arm, erro = _preparar(user_id)
        if erro:
            return erro
        mon = await arm.obter_monitoramento(user_id, monitoramento_id)
        if not mon:
            return _erro("Acompanhamento não encontrado.", 404)
        await arm.remover_monitoramento(user_id, mon["_id"])
        return Response(status_code=204)

    # ------------------------------------------------------------ publicações
    @router.get("/publicacoes/{publicacao_id}")
    async def obter_publicacao(publicacao_id: str, user_id: str = ""):
        """Intimação com o inteiro teor."""
        user_id = user_id.strip()
        arm, erro = _preparar(user_id)
        if erro:
            return erro
        pub = await arm.obter_publicacao(user_id, publicacao_id)
        if not pub:
            return _erro("Intimação não encontrada.", 404)
        return {"publicacao": publicacao_front(pub, completo=True)}

    @router.patch("/publicacoes/{publicacao_id}")
    async def alterar_situacao(publicacao_id: str, body: SituacaoIn):
        """"sem_prazo" = o advogado leu e não há providência; "pendente" desfaz."""
        user_id = body.user_id.strip()
        arm, erro = _preparar(user_id)
        if erro:
            return erro
        if body.situacao not in ("pendente", "sem_prazo"):
            return _erro("Situação inválida.", 400)
        pub = await arm.obter_publicacao(user_id, publicacao_id)
        if not pub:
            return _erro("Intimação não encontrada.", 404)
        if pub.get("situacao") == "agendada":
            return _erro("Esta intimação já tem prazo agendado. Exclua o prazo para mudar a situação.", 409)
        await arm.definir_situacao(user_id, pub["_id"], body.situacao, agora_iso())
        return {"publicacao": publicacao_front({**pub, "situacao": body.situacao}, completo=True)}

    # ------------------------------------------------------------ prazos
    @router.post("/agenda")
    async def criar_prazo(body: NovoPrazoIn):
        user_id = body.user_id.strip()
        arm, erro = _preparar(user_id)
        if erro:
            return erro
        descricao = body.descricao.strip()
        if not descricao or len(descricao) > 200:
            return _erro("Descreva o prazo em até 200 caracteres (ex.: Contestação).", 400)
        data_final = _data_valida(body.data_final)
        if not data_final:
            return _erro("Informe a data final do prazo.", 400)
        caso, erro = await _caso_valido(user_id, body.caso_id)
        if erro:
            return erro

        pub = None
        numero = None
        if body.publicacao_id:
            pub = await arm.obter_publicacao(user_id, body.publicacao_id)
            if not pub:
                return _erro("Intimação não encontrada.", 404)
            numero = pub.get("numero_processo") or None
        elif (body.numero_processo or "").strip():
            numero, problema = normalizar_processo(body.numero_processo)
            if problema:
                return _erro(problema, 400)
        if numero and not caso:
            vinculo = await arm.processo_vinculado(user_id, numero)
            caso = (vinculo or {}).get("caso_id") or None

        momento = agora_iso()
        prazo = await arm.criar_prazo({
            "user_id": user_id, "publicacao_id": str(pub["_id"]) if pub else None, "caso_id": caso,
            "numero_processo": numero, "descricao": descricao, "data_final": data_final,
            "cumprido": False, "cumprido_em": None, "criado_em": momento, "atualizado_em": momento,
        })
        if pub:
            await arm.definir_situacao(user_id, pub["_id"], "agendada", momento)
        return {"prazo": prazo_front(prazo)}

    @router.patch("/agenda/{prazo_id}")
    async def alterar_prazo(prazo_id: str, body: AlteraPrazoIn):
        user_id = body.user_id.strip()
        arm, erro = _preparar(user_id)
        if erro:
            return erro
        prazo = await arm.obter_prazo(user_id, prazo_id)
        if not prazo:
            return _erro("Prazo não encontrado.", 404)
        momento = agora_iso()
        campos: Dict[str, Any] = {"atualizado_em": momento}
        if body.descricao is not None:
            descricao = body.descricao.strip()
            if not descricao or len(descricao) > 200:
                return _erro("Descreva o prazo em até 200 caracteres.", 400)
            campos["descricao"] = descricao
        if body.data_final is not None:
            data_final = _data_valida(body.data_final)
            if not data_final:
                return _erro("Informe a data final do prazo.", 400)
            campos["data_final"] = data_final
        if body.cumprido is not None:
            campos["cumprido"] = body.cumprido
            campos["cumprido_em"] = momento if body.cumprido else None
        await arm.atualizar_prazo(user_id, prazo["_id"], campos)
        return {"prazo": prazo_front({**prazo, **campos})}

    @router.delete("/agenda/{prazo_id}")
    async def remover_prazo(prazo_id: str, user_id: str = ""):
        user_id = user_id.strip()
        arm, erro = _preparar(user_id)
        if erro:
            return erro
        prazo = await arm.obter_prazo(user_id, prazo_id)
        if not prazo:
            return _erro("Prazo não encontrado.", 404)
        await arm.remover_prazo(user_id, prazo["_id"])
        # Sem prazo nenhum, a intimação volta para "a tratar": não some da vista do advogado.
        origem = prazo.get("publicacao_id")
        if origem and not await arm.prazos_da_publicacao(user_id, origem):
            pub = await arm.obter_publicacao(user_id, origem)
            if pub:
                await arm.definir_situacao(user_id, pub["_id"], "pendente", agora_iso())
        return Response(status_code=204)

    return router
