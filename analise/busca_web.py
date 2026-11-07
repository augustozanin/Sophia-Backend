"""
Busca na web restrita a fontes jurídicas e links verificáveis nos cards.

1. A busca da OpenAI só consulta os sites de DOMINIOS (a API aceita até 100; subdomínios entram
   junto). SOPHIA_BUSCA_DOMINIOS="a.jus.br,b.gov.br" troca a lista sem mexer no código.
2. A IA é orientada a pôr no campo "fonte" a URL da página que consultou. Só ficam as URLs que a
   busca realmente devolveu (fontes consultadas e citações da resposta); qualquer outra é apagada,
   para nunca exibir link inventado. Fonte com link aparece clicável no card; sem link, o front
   continua marcando "não verificado".
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, Iterable, List, Set
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

LIMITE_DOMINIOS = 100

# Tribunais superiores e conselhos
_SUPERIORES = ["stf.jus.br", "stj.jus.br", "tst.jus.br", "tse.jus.br", "stm.jus.br",
               "cnj.jus.br", "cjf.jus.br", "csjt.jus.br"]
# Tribunais regionais federais
_TRFS = [f"trf{n}.jus.br" for n in range(1, 7)]
# Tribunais de Justiça dos estados e do DF
_TJS = [f"tj{uf}.jus.br" for uf in (
    "ac", "al", "ap", "am", "ba", "ce", "dft", "es", "go", "ma", "mt", "ms", "mg", "pa", "pb",
    "pr", "pe", "pi", "rj", "rn", "rs", "ro", "rr", "sc", "sp", "se", "to")]
# Tribunais regionais do trabalho
_TRTS = [f"trt{n}.jus.br" for n in range(1, 25)]
# Legislação oficial
_LEGISLACAO = ["planalto.gov.br", "lexml.gov.br", "normas.leg.br", "senado.leg.br",
               "camara.leg.br", "in.gov.br"]
# Governo federal, agências e órgãos (gov.br cobre os órgãos em www.gov.br/..., como o INSS)
_ORGAOS = ["gov.br", "bcb.gov.br", "consumidor.gov.br", "ans.gov.br", "anatel.gov.br",
           "aneel.gov.br", "anac.gov.br", "mpf.mp.br", "cnmp.mp.br", "oab.org.br"]
# Secundários: resumos, íntegras, notícias e doutrina (não são fonte primária)
_SECUNDARIOS = ["dizerodireito.com.br", "jusbrasil.com.br", "conjur.com.br", "migalhas.com.br",
                "jota.info", "ibdfam.org.br", "scielo.br"]

DOMINIOS: List[str] = (_SUPERIORES + _TRFS + _TJS + _TRTS + _LEGISLACAO + _ORGAOS
                       + _SECUNDARIOS)


def dominios_da_busca() -> List[str]:
    """Lista de sites liberados para a busca (variável de ambiente ou a lista padrão)."""
    bruto = (os.environ.get("SOPHIA_BUSCA_DOMINIOS") or "").strip()
    itens = [d for d in re.split(r"[,\s]+", bruto) if d] if bruto else DOMINIOS
    limpos: List[str] = []
    for d in itens:
        d = re.sub(r"^https?://", "", d.strip().lower()).strip("/")
        if d and d not in limpos:
            limpos.append(d)
    return limpos[:LIMITE_DOMINIOS]


INSTRUCAO_LINKS = (
    "\n\nBUSCA NA WEB: pesquise em fontes oficiais (tribunais, legislação) e, quando confirmar uma "
    "tese, tema, súmula ou julgado numa página consultada, coloque no campo \"fonte\" a referência "
    "seguida da URL exata dessa página (https://...). Nunca escreva uma URL que você não abriu na "
    "busca. Se não encontrar a página, mantenha \"não verificado\" e siga a regra 2.")

_URL_RE = re.compile(r"https?://[^\s\"'<>()\[\]]+")
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
_PARAMS_DE_RASTREIO = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}


def normalizar_url(url: str) -> str:
    """Forma comparável: sem esquema, www, fragmento, parâmetros de rastreio e barra final."""
    url = url.strip().rstrip(".,;:")
    try:
        p = urlsplit(url)
    except ValueError:
        return url.lower()
    host = (p.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    query = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                       if k.lower() not in _PARAMS_DE_RASTREIO])
    return urlunsplit(("", host, p.path.rstrip("/"), query, "")).lstrip("/")


def urls_consultadas(urls: Iterable[str]) -> Set[str]:
    return {normalizar_url(u) for u in urls if u}


def _url_limpa(url: str) -> str:
    """URL para exibir: sem parâmetros de rastreio (a OpenAI acrescenta utm_source=openai)."""
    url = url.strip().rstrip(".,;:")
    try:
        p = urlsplit(url)
    except ValueError:
        return url
    query = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                       if k.lower() not in _PARAMS_DE_RASTREIO])
    return urlunsplit((p.scheme, p.netloc, p.path, query, p.fragment))


def _limpar_fonte(fonte: str, consultadas: Set[str]) -> str:
    texto = _MD_LINK_RE.sub(lambda m: m.group(2), fonte)  # [site](url) -> url

    def trocar(m: re.Match) -> str:
        url = m.group(0)
        return _url_limpa(url) if normalizar_url(url) in consultadas else ""

    texto = _URL_RE.sub(trocar, texto)
    texto = re.sub(r"\(\s*\)", "", texto)
    return re.sub(r"\s{2,}", " ", texto).strip(" ,;-–—")


def validar_links(dados: Dict[str, Any], consultadas: Set[str]) -> Dict[str, Any]:
    """Mantém no campo "fonte" só as URLs que a busca devolveu. Altera e devolve `dados`."""
    for chave in ("teses", "temas_stf_stj", "jurisprudencia"):
        for item in dados.get(chave) or []:
            if isinstance(item, dict) and isinstance(item.get("fonte"), str):
                limpa = _limpar_fonte(item["fonte"], consultadas)
                item["fonte"] = limpa or "não verificado"
    return dados
