"""
Cliente da API pública de comunicações processuais do CNJ (Comunica PJe), a mesma que
alimenta o DJEN. A consulta não exige autenticação.

    GET https://comunicaapi.pje.jus.br/api/v1/comunicacao
        ?numeroOab=&ufOab=  ou  ?numeroProcesso=
        &dataDisponibilizacaoInicio=AAAA-MM-DD&dataDisponibilizacaoFim=AAAA-MM-DD
        &itensPorPagina=100&pagina=1

Limites observados em 11/2026: 20 requisições por janela, por IP (cabeçalho
`X-RateLimit-Limit`), e 429 ao estourar. Por isso as páginas são pedidas em sequência,
com teto por consulta, e um 429 interrompe a sincronização em vez de insistir.
"""
from __future__ import annotations

import html
import os
import re
from html.parser import HTMLParser
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import httpx

URL_DJEN = os.getenv("DJEN_API_URL", "https://comunicaapi.pje.jus.br/api/v1/comunicacao").strip()
ITENS_POR_PAGINA = 100
LIMITE_TEXTO = 20_000

# (parâmetros) -> (status HTTP, corpo JSON ou None). Injetável nos testes.
Buscar = Callable[[Dict[str, Any]], Awaitable[Tuple[int, Optional[Dict[str, Any]]]]]


class ErroDjen(Exception):
    def __init__(self, mensagem: str, limite: bool = False) -> None:
        super().__init__(mensagem)
        self.limite = limite


async def buscar_http(parametros: Dict[str, Any]) -> Tuple[int, Optional[Dict[str, Any]]]:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as cliente:
            resposta = await cliente.get(URL_DJEN, params=parametros,
                                         headers={"Accept": "application/json", "User-Agent": "Sophia/1.0"})
    except httpx.HTTPError as exc:
        detalhe = f"{exc.__class__.__name__}: {exc}" if str(exc) else exc.__class__.__name__
        raise ErroDjen(f"Não foi possível falar com o DJEN ({detalhe}).") from exc
    try:
        corpo = resposta.json()
    except ValueError:
        # Guarda o começo do que veio (HTML de bloqueio, por exemplo) para a mensagem de erro.
        corpo = {"_texto": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", resposta.text or "")).strip()[:300]}
    return resposta.status_code, corpo


def _detalhe_da_resposta(corpo: Optional[Dict[str, Any]]) -> str:
    """O que a API disse, para entrar na mensagem: `message`, texto cru ou nada."""
    if not isinstance(corpo, dict):
        return ""
    for chave in ("message", "mensagem", "error", "_texto"):
        valor = corpo.get(chave)
        if isinstance(valor, str) and valor.strip():
            return f": {valor.strip()[:300]}"
    return ""


async def buscar_comunicacoes(buscar: Buscar, filtros: Dict[str, str], max_paginas: int) -> List[Dict[str, Any]]:
    """Todas as páginas da consulta, até `max_paginas`. Itens crus da API."""
    itens: List[Dict[str, Any]] = []
    for pagina in range(1, max_paginas + 1):
        status, corpo = await buscar({**filtros, "itensPorPagina": ITENS_POR_PAGINA, "pagina": pagina})
        detalhe = _detalhe_da_resposta(corpo)
        if status == 429:
            raise ErroDjen("O DJEN limitou as consultas por alguns instantes. Tente de novo em 1 minuto.", limite=True)
        if status == 403:
            raise ErroDjen("O DJEN recusou a consulta deste servidor (HTTP 403). Ele pode bloquear acessos de "
                           f"fora do Brasil{detalhe}")
        if status != 200 or not isinstance(corpo, dict) or "_texto" in corpo:
            raise ErroDjen(f"O DJEN respondeu com erro (HTTP {status}, página {pagina}){detalhe}")
        lote = corpo.get("items") or []
        if not isinstance(lote, list):
            raise ErroDjen(f"O DJEN devolveu uma resposta em formato inesperado (sem lista de itens){detalhe}")
        itens.extend(item for item in lote if isinstance(item, dict))
        total = corpo.get("count")
        if len(lote) < ITENS_POR_PAGINA or (isinstance(total, int) and len(itens) >= total):
            break
    return itens


# ---------------------------------------------------------------- texto da intimação
_BLOCOS = {"p", "div", "br", "tr", "section", "article", "header", "footer", "li", "h1", "h2", "h3", "h4",
           "table", "hr"}


class _Extrator(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: List[str] = []
        self._ignorar = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script", "head"):
            self._ignorar += 1
        elif tag in _BLOCOS:
            self.partes.append("\n")
        elif tag == "td":
            self.partes.append(" ")

    def handle_endtag(self, tag):
        if tag in ("style", "script", "head"):
            self._ignorar = max(0, self._ignorar - 1)
        elif tag in _BLOCOS:
            self.partes.append("\n")

    def handle_data(self, data):
        if not self._ignorar:
            self.partes.append(data)


def texto_puro(conteudo: object) -> str:
    """O DJEN manda o teor em HTML. Vira texto com quebras de parágrafo e sem espaços sobrando."""
    bruto = str(conteudo or "")
    if "<" in bruto:
        extrator = _Extrator()
        extrator.feed(bruto)
        extrator.close()
        bruto = "".join(extrator.partes)
    bruto = html.unescape(bruto).replace("\xa0", " ")
    linhas = [re.sub(r"[ \t\r\f\v]+", " ", linha).strip() for linha in bruto.split("\n")]
    texto = re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()
    return texto[:LIMITE_TEXTO]


def _data_iso(item: Dict[str, Any]) -> Optional[str]:
    valor = str(item.get("data_disponibilizacao") or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor):
        return valor
    brasileira = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", str(item.get("datadisponibilizacao") or "").strip())
    if brasileira:
        dia, mes, ano = brasileira.groups()
        return f"{ano}-{mes}-{dia}"
    return None


def normalizar(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Só o que a tela usa, com nomes nossos. None quando falta id ou data (item inútil)."""
    djen_id = item.get("id")
    data = _data_iso(item)
    if not isinstance(djen_id, int) or not data:
        return None
    advogados = []
    for vinculo in item.get("destinatarioadvogados") or []:
        advogado = (vinculo or {}).get("advogado") or {}
        if advogado.get("nome"):
            advogados.append({"nome": str(advogado.get("nome")), "oab": str(advogado.get("numero_oab") or ""),
                              "uf": str(advogado.get("uf_oab") or "")})
    partes = [{"nome": str(d.get("nome")), "polo": str(d.get("polo") or "")}
              for d in item.get("destinatarios") or [] if isinstance(d, dict) and d.get("nome")]
    link = str(item.get("link") or "").strip()
    return {
        "djen_id": djen_id,
        "data_disponibilizacao": data,
        "tribunal": str(item.get("siglaTribunal") or "").strip(),
        "orgao": str(item.get("nomeOrgao") or "").strip(),
        "tipo_comunicacao": str(item.get("tipoComunicacao") or "").strip(),
        "tipo_documento": str(item.get("tipoDocumento") or "").strip(),
        "classe": str(item.get("nomeClasse") or "").strip(),
        "numero_processo": re.sub(r"\D", "", str(item.get("numero_processo") or "")),
        "texto": texto_puro(item.get("texto")),
        "link": link if link.startswith("https://") else None,
        "advogados": advogados[:20],
        "partes": partes[:20],
        "cancelada": item.get("ativo") is False or bool(item.get("data_cancelamento")),
        "motivo_cancelamento": str(item.get("motivo_cancelamento") or "").strip() or None,
    }
