"""
Peças comuns dos catálogos de precedentes: construtores de item e de sub-área e URLs oficiais.

Campos de cada precedente (ver `precedentes.py`): identificador, nível (N1/N2/N3), espécie, status
e motivo, título, fato-tipo em linguagem leiga, tese resumida, alerta, busca e fonte oficial.
"""
from __future__ import annotations

from typing import Any, Dict, List


def p(id: str, nivel: str, especie: str, status: str, motivo: str, titulo: str, fato: str,
      tese: str, busca: str, fonte: str, alerta: str = "") -> Dict[str, str]:
    return {"id": id, "nivel": nivel, "especie": especie, "status": status, "motivo": motivo,
            "titulo": titulo, "fato": fato, "tese": tese, "alerta": alerta, "busca": busca, "fonte": fonte}


def sub(id: str, nome: str, palavras: List[str], precedentes: List[Dict[str, str]],
        lacunas: str = "") -> Dict[str, Any]:
    return {"id": id, "nome": nome, "palavras": palavras, "precedentes": precedentes, "lacunas": lacunas}


def stj(n: int) -> str:
    return ("https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?novaConsulta=true"
            f"&tipo_pesquisa=T&cod_tema_inicial={n}&cod_tema_final={n}")


def stf(n: int) -> str:
    return f"https://portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num={n}"


def stj_sumula(n: int) -> str:
    return f"https://scon.stj.jus.br/SCON/sumstj/toc.jsp?sumula={n}"


def tnu_sumula(n: int) -> str:
    return f"https://www.cjf.jus.br/phpdoc/virtus/sumula.php?nsul={n}"


def tnu_tema(n: int) -> str:
    return ("https://www.cjf.jus.br/cjf/corregedoria-da-justica-federal/turma-nacional-de-uniformizacao/"
            f"temas-representativos?tema={n}")
