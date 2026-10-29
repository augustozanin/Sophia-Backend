"""
Traduz o JSON da IA (analysis.py) para o modelo `AnalisePreliminar` do front
(src/lib/api/analise.ts). Regra do contrato: item sem fonte verificável chega com
`fontes` vazio — o front o marca como "não verificado"; nunca se esconde nem se inventa.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional

_TRIBUNAL_RE = re.compile(r"\b(STF|STJ|TST|TSE|STM|TRF\s?\d|TRT\s?\d+|TJ[A-Z]{2}|TRE-?[A-Z]{2})\b")
_URL_RE = re.compile(r"https?://\S+")
_NIVEIS = {"alta", "media", "baixa"}
_POSICOES = {"majoritaria", "minoritaria", "em_analise"}


def _norm(s: Any) -> str:
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower().strip()


def _nivel(valor: Any, padrao: str = "media") -> str:
    v = _norm(valor)
    return v if v in _NIVEIS else padrao


def _data_iso(valor: Any) -> Optional[str]:
    texto = str(valor or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _fontes(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    fonte = str(item.get("fonte") or "").strip()
    if not fonte or "nao verificado" in _norm(fonte):
        return []
    achado = _TRIBUNAL_RE.search(fonte)
    tribunal = str(item.get("tribunal") or "").strip() or (achado.group(1) if achado else "Fonte citada")
    url = _URL_RE.search(fonte)
    out: Dict[str, Any] = {"tribunal": tribunal, "identificador": _URL_RE.sub("", fonte).strip(" ,;()") or fonte}
    data = _data_iso(item.get("data"))
    if data:
        out["data"] = data
    if url:
        out["url"] = url.group(0).rstrip(".,;)")
    return [out]


def _posicao(valor: Any) -> Optional[str]:
    v = _norm(valor)
    if v == "minoritaria_em_analise":  # valor do schema antigo
        v = "em_analise"
    return v if v in _POSICOES else None


def para_analise_front(registro: Dict[str, Any], caso_id: str) -> Dict[str, Any]:
    """registro = documento da coleção `analises` ({versao, gerada_em, analise})."""
    dados = registro["analise"]
    versao = registro["versao"]
    insights: List[Dict[str, Any]] = []

    def novo(categoria: str, titulo: str, detalhe: str, relevancia: str, **extra) -> None:
        insight = {"id": f"{caso_id}-v{versao}-{len(insights) + 1}", "categoria": categoria,
                   "titulo": titulo or "(sem título)", "detalhe": detalhe or "",
                   "relevancia": relevancia, "fontes": extra.pop("fontes", [])}
        insight.update({k: v for k, v in extra.items() if v})
        insights.append(insight)

    for t in dados.get("teses", []):
        novo("tese", t.get("titulo"), t.get("descricao"), _nivel(t.get("relevancia")), fontes=_fontes(t))
    for t in dados.get("temas_stf_stj", []):
        novo("tema_superior", t.get("titulo"), t.get("descricao"), _nivel(t.get("relevancia")), fontes=_fontes(t))
    for j in dados.get("jurisprudencia", []):
        meta = None
        if j.get("processo") or j.get("tribunal"):
            meta = [str(j.get("tribunal") or "Processo"), str(j.get("processo") or j.get("data") or "")]
        novo("jurisprudencia", j.get("titulo"), j.get("resumo"), "media", fontes=_fontes(j),
             posicaoJurisprudencial=_posicao(j.get("status")), meta=meta)
    for p in dados.get("perguntas_sugeridas", []):
        novo("pergunta", p.get("pergunta"), p.get("objetivo"), "media")
    rotulos = {"pericia": "Perícia", "documento_faltante": "Documento faltante",
               "possibilidade_de_acordo": "Possibilidade de acordo", "outro": "Necessidade adicional"}
    for n in dados.get("necessidades_adicionais", []):
        tipo = _norm(n.get("tipo"))
        categoria = "acordo" if tipo == "possibilidade_de_acordo" else "necessidade"
        # Relevância qualitativa; nenhum percentual de êxito é exposto (contrato de API).
        novo(categoria, rotulos.get(tipo, rotulos["outro"]), n.get("descricao"), _nivel(n.get("probabilidade")))

    return {
        "id": f"{caso_id}-analise-{versao}",
        "casoId": caso_id,
        "versao": versao,
        "geradaEm": registro["gerada_em"],
        "resumo": str(dados.get("resumo_caso") or ""),
        "insights": insights,
        "demonstracao": False,
        "origem": "chat" if registro.get("origem") == "chat" else "relato",
    }


def mensagem_front(m: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": m["id"], "papel": "advogado" if m["papel"] == "user" else "assistente",
            "conteudo": m["conteudo"], "criadaEm": m["criada_em"]}


def modelo_front(m: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": m["id"], "nome": m["nome"], "grupo": m["grupo"], "fase": m["fase"],
            "descricao": m["descricao"], "quandoUsar": m["quando_usar"],
            "baseLegal": list(m.get("base_legal") or []), "prazo": m.get("prazo"),
            "secoes": list(m.get("secoes") or [])}


def peca_front(p: Dict[str, Any], com_texto: bool = True) -> Dict[str, Any]:
    """Minuta salva na coleção `pecas`. A listagem não carrega o texto inteiro."""
    out = {"id": p["id"], "modeloId": p["modelo_id"], "titulo": p["titulo"],
           "geradaEm": p["gerada_em"], "analiseVersao": p.get("analise_versao")}
    if p.get("instrucoes"):
        out["instrucoes"] = p["instrucoes"]
    if com_texto:
        out["texto"] = p["texto"]
    return out
