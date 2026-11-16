"""
Precedentes curados por área na análise, no chat e na minuta: seleção das sub-áreas ligadas ao
caso e montagem do trecho do prompt. Os dados ficam em analise/catalogo/, um módulo por área.

Cada precedente foi conferido na data de verificação da área nos portais oficiais:
número, órgão, tese e situação. Quando só deu para conferir em fonte secundária, o item diz
isso no status ou no alerta. A seleção segue três níveis de autoridade:

- N1: vinculante nacional (STF em repercussão geral ou controle concentrado; STJ em repetitivo).
- N2: uniformização (TNU nos Juizados Especiais Federais; súmulas do STJ, CPC art. 927, IV).
- N3: regional da 4ª Região (TRF4, TRU4; TJs de RS, SC e PR). Vale só lá.

Status: VIGENTE | EM ATENÇÃO (embargos, mérito pendente, trânsito não conferido) | ALTERADO
(vale a versão nova descrita) | SUPERADO (só como alerta) | NÃO VERIFICADO (pista a confirmar).

Só as sub-áreas ligadas ao caso entram no prompt (palavras-chave no relato), no máximo
LIMITE_SUBAREAS, para caber no limite de tokens do provedor. Sem texto do caso, nada entra.

Para atualizar: reabra cada URL, confira a situação, ajuste o status e o VERIFICADO do módulo da
área. Itens com status EM ATENÇÃO são os primeiros a revisar.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List

from .catalogo import (administrativo, ambiental, civil, consumidor, digital, empresarial, familia,
                       imobiliario, penal, previdenciario, trabalhista, tributario)

# Data padrão de verificação; cada módulo de catalogo/ pode declarar a sua em VERIFICADO.
VERIFICADO_EM = "16/11/2026"
LIMITE_SUBAREAS = 3
# Caracteres do bloco de precedentes por tarefa (~4 por token). A sub-área mais ligada ao caso
# sempre entra; as seguintes só se couberem. Protege o limite de tokens por minuto do Groq gratuito.
ORCAMENTO = {"analise": 9_000, "chat": 6_500, "minuta": 6_500}
STATUS = ("VIGENTE", "EM ATENÇÃO", "ALTERADO", "SUPERADO", "NÃO VERIFICADO")
NIVEIS = ("N1", "N2", "N3")

# Um módulo por área em analise/catalogo/: SUBAREAS, ALCANCE e, opcionalmente, VERIFICADO.
_MODULOS = {
    "previdenciario": previdenciario, "consumidor": consumidor, "civil": civil,
    "familia-sucessoes": familia, "trabalhista": trabalhista, "penal": penal, "tributario": tributario,
    "administrativo": administrativo, "imobiliario": imobiliario, "ambiental": ambiental,
    "digital": digital, "empresarial": empresarial,
}
CATALOGO: Dict[str, List[Dict[str, Any]]] = {area: m.SUBAREAS for area, m in _MODULOS.items()}
_ALCANCE_REGIONAL: Dict[str, str] = {area: m.ALCANCE for area, m in _MODULOS.items()}
_DATA_POR_AREA: Dict[str, str] = {area: getattr(m, "VERIFICADO", VERIFICADO_EM) for area, m in _MODULOS.items()}

_CABECALHO = """\
PRECEDENTES CURADOS DESTA ÁREA (pesquisa da equipe Sophia; situação conferida em {data} nos portais \
oficiais e sujeita a mudança depois disso). Entram só as sub-áreas ligadas aos fatos. São PONTO DE \
PARTIDA, NÃO LISTA FECHADA: considere também outras teses aplicáveis a estes fatos, ainda que fora \
desta lista. Como usar:
- Use um precedente só se o fato-tipo corresponder ao relato. Não force.
- VIGENTE: pode fundamentar. Em "fonte", escreva o identificador e a URL indicada.
- EM ATENÇÃO: use com a ressalva do motivo.
- ALTERADO: aplique só a versão atual descrita.
- SUPERADO: nunca como fundamento favorável; só como alerta, dizendo por quê.
- NÃO VERIFICADO: não cite o número; é pista a confirmar.
- N1 (vinculante nacional) prevalece sobre N2 (uniformização) e N3 ({alcance}). Diga se é tese, \
súmula ou IRDR: não são a mesma coisa.
- Precedente fora desta lista continua sujeito às regras 1 e 2."""

_EXTRA_POR_TAREFA = {
    "analise": ("- No JSON, cada precedente desta lista que você usar vai em \"temas_stf_stj\" (nunca em "
                "\"jurisprudencia\"), com tribunal, identificador (ex.: Tema 1124), espécie, o nível N1/N2/N3 "
                "indicado e a situação (VIGENTE → vigente, EM ATENÇÃO → em_atencao, ALTERADO → alterado, "
                "SUPERADO → superado). O mesmo vale para outros temas, súmulas e IRDR que achar na busca.\n"
                "- Com busca na web ativa: pesquise cada precedente que usar (a \"Busca\" indicada ajuda) para "
                "confirmar a situação e pegar a URL da página oficial aberta, e pesquise além da lista. Sem "
                "busca: use a URL do catálogo; o que estiver fora da lista segue as regras 1 e 2."),
    "chat": "- Ao responder, diga a situação (status) do precedente e a data de verificação.",
    "minuta": ("- Na peça, fundamente com VIGENTE. EM ATENÇÃO só se favorecer o cliente, sem dizer que é "
               "definitivo. SUPERADO e NÃO VERIFICADO nunca como fundamento; se a outra parte puder "
               "invocar um SUPERADO, rebata."),
}


def _normalizar(texto: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return texto.lower()


def _padroes(sub: Dict[str, Any]) -> List[re.Pattern]:
    cache = sub.get("_padroes")
    if cache is None:
        cache = [re.compile(p if p.startswith(r"\b") else r"\b" + p) for p in sub["palavras"]]
        sub["_padroes"] = cache
    return cache


def subareas_relevantes(area_id: str, texto_caso: str, limite: int = LIMITE_SUBAREAS) -> List[Dict[str, Any]]:
    """Sub-áreas cujas palavras-chave aparecem no caso, da mais citada para a menos (máx. `limite`)."""
    texto = _normalizar(texto_caso)
    if not texto.strip():
        return []
    pontuadas = []
    for ordem, sub in enumerate(CATALOGO.get(area_id, [])):
        pontos = sum(1 for padrao in _padroes(sub) if padrao.search(texto))
        if pontos:
            pontuadas.append((-pontos, ordem, sub))
    pontuadas.sort(key=lambda item: (item[0], item[1]))
    return [sub for _, _, sub in pontuadas[:limite]]


def _linha(p: Dict[str, str], tarefa: str) -> str:
    cabeca = f"- [{p['nivel']} · {p['id']} · {p['especie']} · {p['status']}: {p['motivo']}] {p['titulo']}"
    partes = [cabeca]
    if tarefa == "analise":
        partes.append(f"  Fato-tipo: {p['fato']}")
    partes.append(f"  Tese: {p['tese']}")
    if p["alerta"]:
        partes.append(f"  Alerta: {p['alerta']}")
    if tarefa == "analise":
        partes.append(f"  Busca: {p['busca']}")
    partes.append(f"  Fonte: {p['fonte']}")
    return "\n".join(partes)


def bloco_precedentes(area_id: str, tarefa: str, texto_caso: str) -> str:
    """Trecho do prompt com os precedentes das sub-áreas ligadas ao caso. Vazio se nenhuma."""
    subareas = subareas_relevantes(area_id, texto_caso)
    if not subareas:
        return ""
    partes = [_CABECALHO.format(data=_DATA_POR_AREA.get(area_id, VERIFICADO_EM),
                                alcance=_ALCANCE_REGIONAL.get(area_id, "regional"))]
    extra = _EXTRA_POR_TAREFA.get(tarefa)
    if extra:
        partes[0] += "\n" + extra
    orcamento = ORCAMENTO.get(tarefa, ORCAMENTO["analise"])
    usado = len(partes[0])
    for indice, sub in enumerate(subareas):
        linhas = [f"SUB-ÁREA: {sub['nome'].upper()}"]
        linhas += [_linha(p, tarefa) for p in sub["precedentes"]]
        if sub["lacunas"]:
            linhas.append(f"- {sub['lacunas']}")
        trecho = "\n".join(linhas)
        if indice and usado + len(trecho) > orcamento:
            continue
        partes.append(trecho)
        usado += len(trecho) + 2
    return "\n\n".join(partes)


def urls_do_catalogo(area_id: Any) -> List[str]:
    """URLs oficiais já conferidas desta área. Entram como 'consultadas' na validação de links:
    a fonte do catálogo pode aparecer clicável no card mesmo sem busca na web."""
    return [p["fonte"] for sub in CATALOGO.get(str(area_id or ""), []) for p in sub["precedentes"]]
