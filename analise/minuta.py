"""
Minuta de peça em formato estruturado.

A IA devolve um JSON com as partes da peça (endereçamento, qualificação, título, seções, fecho) e
o próprio backend monta o texto e o .docx no padrão usual das petições. Assim o leiaute não depende
do modelo e nunca sai JSON cru na minuta.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

TIPOS_DE_BLOCO = ("paragrafo", "subtitulo", "citacao", "lista")

SCHEMA_MINUTA = """\
{
  "enderecamento": "EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) ... (em maiúsculas; null em peça extrajudicial sem destinatário)",
  "referencia": "Processo nº [NÚMERO DO PROCESSO] (quando a peça é num processo já existente) ou null",
  "qualificacao": ["parágrafo(s) do preâmbulo: partes qualificadas e o pedido de abertura, ex.: 'FULANO, ..., vem, respeitosamente, à presença de Vossa Excelência, por seu advogado, propor'"],
  "titulo": "NOME DA PEÇA OU DA AÇÃO EM MAIÚSCULAS",
  "complemento_titulo": "texto após o título, ex.: 'em face de [NOME DO RÉU], ..., pelos fatos e fundamentos a seguir expostos.' ou null",
  "secoes": [
    {"titulo": "DOS FATOS", "blocos": [
      {"tipo": "paragrafo", "texto": "..."},
      {"tipo": "subtitulo", "texto": "Da aposentadoria híbrida"},
      {"tipo": "citacao", "texto": "trecho literal de lei ou ementa", "fonte": "STJ, REsp ... ou Lei ..., art. ..."},
      {"tipo": "lista", "itens": ["a concessão de ...", "a condenação de ..."]}
    ]}
  ],
  "fecho": {"encerramento": "Nestes termos, pede deferimento.", "local_data": "[CIDADE], [DATA].",
            "advogado": "[NOME DO ADVOGADO]", "oab": "OAB/[UF] nº [NÚMERO]"}
}"""

DRAFT_SYSTEM_SUFFIX = f"""\
TAREFA: MINUTA DE PEÇA. Gere um RASCUNHO de peça processual ou extrajudicial com base no contexto \
já consolidado do caso. Reaproveite fielmente teses, jurisprudência e dados já validados na análise; \
NÃO re-derive nem invente artigos de lei, datas, valores ou dados técnicos que não estejam no \
contexto. Quando faltar um dado (nome, CPF, endereço, número do processo, juízo, datas, valores), \
escreva um marcador entre colchetes, como [NOME DO RÉU] ou [NÚMERO DO PROCESSO], em vez de inventar. \
As referências legais do modelo são só orientação: cite apenas as que se aplicam ao caso.

FORMATO: o schema JSON da regra 8 é da análise e NÃO vale aqui. Responda APENAS com um único objeto \
JSON válido NESTE schema de minuta, sem markdown e sem texto fora do JSON:
{SCHEMA_MINUTA}

REGRAS DE REDAÇÃO:
- Linguagem forense formal, clara e objetiva, em português do Brasil, em terceira pessoa \
("o Autor", "a Ré"); parágrafos completos, sem tópicos soltos fora de "lista".
- Siga a ESTRUTURA DO MODELO na mesma ordem. "Endereçamento", "Qualificação das partes" e "Fecho" \
vão nos campos próprios; cada uma das demais etapas vira uma seção em "secoes", com título em \
maiúsculas no padrão "DOS FATOS", "DO DIREITO", "DOS PEDIDOS" (sem numeração: o sistema numera).
- Os pedidos vão numa seção "DOS PEDIDOS" com um parágrafo introdutório ("Diante do exposto, \
requer:") e um bloco "lista" com um pedido por item (sem letras: o sistema coloca a), b), c)...).
- Use "citacao" só para trecho literal de lei, súmula ou ementa que esteja no contexto, com a fonte.
- O valor da causa, quando o modelo pedir, vai numa seção "DO VALOR DA CAUSA".
- Não escreva o aviso de minuta: o sistema já o inclui."""


def _texto(valor: Any) -> str:
    return re.sub(r"[ \t]+", " ", str(valor or "")).strip()


def _sem_numeracao(titulo: str) -> str:
    """Tira "1.", "I -", "II –" do começo: a numeração das seções é do sistema."""
    return re.sub(r"^\s*(?:[IVXLC]+|\d+)\s*[\.\-–—)]\s*", "", titulo).strip()


def normalizar_minuta(dados: Any) -> Dict[str, Any]:
    """Limpa e padroniza o JSON da IA. Levanta ValueError se faltar o essencial."""
    if not isinstance(dados, dict):
        raise ValueError("A minuta deve ser um objeto JSON.")
    secoes: List[Dict[str, Any]] = []
    for secao in dados.get("secoes") or []:
        if not isinstance(secao, dict):
            continue
        blocos: List[Dict[str, Any]] = []
        for bloco in secao.get("blocos") or []:
            if isinstance(bloco, str):
                bloco = {"tipo": "paragrafo", "texto": bloco}
            if not isinstance(bloco, dict):
                continue
            tipo = bloco.get("tipo") if bloco.get("tipo") in TIPOS_DE_BLOCO else "paragrafo"
            if tipo == "lista":
                itens = [re.sub(r"^\s*(?:[a-z]\)|\d+[\.\)]|[-•])\s*", "", _texto(i))
                         for i in bloco.get("itens") or []]
                itens = [i for i in itens if i]
                if itens:
                    blocos.append({"tipo": "lista", "itens": itens})
                continue
            texto = _texto(bloco.get("texto"))
            if not texto:
                continue
            novo = {"tipo": tipo, "texto": texto}
            if tipo == "citacao" and _texto(bloco.get("fonte")):
                novo["fonte"] = _texto(bloco.get("fonte"))
            blocos.append(novo)
        titulo = _sem_numeracao(_texto(secao.get("titulo"))).upper()
        if titulo and blocos:
            secoes.append({"titulo": titulo, "blocos": blocos})
    titulo = _texto(dados.get("titulo")).upper()
    if not titulo:
        raise ValueError('A minuta não trouxe o "titulo" da peça.')
    if not secoes:
        raise ValueError('A minuta não trouxe nenhuma seção com texto em "secoes".')
    qualificacao = dados.get("qualificacao") or []
    if isinstance(qualificacao, str):
        qualificacao = [qualificacao]
    fecho = dados.get("fecho") if isinstance(dados.get("fecho"), dict) else {}
    return {
        "enderecamento": _texto(dados.get("enderecamento")).upper() or None,
        "referencia": _texto(dados.get("referencia")) or None,
        "qualificacao": [_texto(p) for p in qualificacao if _texto(p)],
        "titulo": titulo,
        "complemento_titulo": _texto(dados.get("complemento_titulo")) or None,
        "secoes": secoes,
        "fecho": {
            "encerramento": _texto(fecho.get("encerramento")) or "Nestes termos, pede deferimento.",
            "local_data": _texto(fecho.get("local_data")) or "[CIDADE], [DATA].",
            "advogado": _texto(fecho.get("advogado")) or "[NOME DO ADVOGADO]",
            "oab": _texto(fecho.get("oab")) or "OAB/[UF] nº [NÚMERO]",
        },
    }


def ler_minuta(raw: str) -> Dict[str, Any]:
    raw = (raw or "").strip()
    try:
        dados = json.loads(raw)
    except json.JSONDecodeError:
        achado = re.search(r"\{.*\}", raw, re.DOTALL)
        if not achado:
            raise ValueError("A resposta da IA não veio no formato da minuta (JSON).")
        try:
            dados = json.loads(achado.group(0))
        except json.JSONDecodeError as e:
            raise ValueError("A resposta da IA não veio no formato da minuta (JSON).") from e
    if isinstance(dados, dict) and "teses" in dados and "secoes" not in dados:
        raise ValueError("A IA devolveu o JSON da análise em vez da minuta: use o schema de minuta.")
    return normalizar_minuta(dados)


_ROMANOS = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def romano(n: int) -> str:
    saida = ""
    for valor, letra in [(50, "L"), (40, "XL")] + _ROMANOS:
        while n >= valor:
            saida += letra
            n -= valor
    return saida


def letra(i: int) -> str:
    """a, b, ..., z, aa, ab..."""
    return ("" if i < 26 else letra(i // 26 - 1)) + "abcdefghijklmnopqrstuvwxyz"[i % 26]


def titulo_da_secao(indice: int, titulo: str) -> str:
    return f"{romano(indice + 1)} – {titulo}"


def texto_da_minuta(m: Dict[str, Any]) -> str:
    """Versão em texto (tela e "Copiar texto"): uma linha por parágrafo, títulos em maiúsculas."""
    linhas: List[str] = []
    if m.get("enderecamento"):
        linhas += [m["enderecamento"], ""]
    if m.get("referencia"):
        linhas += [m["referencia"], ""]
    for p in m.get("qualificacao") or []:
        linhas += [p, ""]
    linhas += [m["titulo"], ""]
    if m.get("complemento_titulo"):
        linhas += [m["complemento_titulo"], ""]
    for i, secao in enumerate(m["secoes"]):
        linhas += [titulo_da_secao(i, secao["titulo"]), ""]
        for bloco in secao["blocos"]:
            if bloco["tipo"] == "lista":
                linhas += [f"{letra(j)}) {item}" for j, item in enumerate(bloco["itens"])] + [""]
            elif bloco["tipo"] == "citacao":
                fonte = f" ({bloco['fonte']})" if bloco.get("fonte") else ""
                linhas += [f"“{bloco['texto']}”{fonte}", ""]
            else:
                linhas += [bloco["texto"], ""]
    f = m["fecho"]
    linhas += [f["encerramento"], "", f["local_data"], "", f["advogado"], f["oab"]]
    return "\n".join(linhas).strip()
