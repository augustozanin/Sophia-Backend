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
TAREFA: MINUTA DE PEÇA. Nesta tarefa o seu papel muda: você deixa de ser o analista neutro da análise \
preliminar e passa a ser o ADVOGADO DA PARTE CLIENTE, redigindo um rascunho que o advogado vai revisar \
e assinar. A peça é parcial por natureza: o objetivo é o melhor resultado possível para o cliente, \
dentro da lei e da ética profissional. Use o contexto consolidado do caso (relato, análise e \
instruções do advogado). As regras 1 a 7 continuam valendo para fontes e dados; a regra 8 (JSON da \
análise) e a postura neutra da análise não valem aqui.

ESTRATÉGIA DE ADVOGADO (aplique o que couber ao tipo de peça e ao lado do cliente):
- Fatos: narre sob a ótica do cliente. Comece pelo que mais o favorece; destaque a conduta da outra \
parte, o dano e a vulnerabilidade do cliente; dê contexto aos fatos desfavoráveis em vez de expô-los \
soltos. Não admita nem conceda o que o relato não obriga a admitir, e não aponte fraquezas do próprio \
cliente: elas ficam na análise, para o advogado, não na peça.
- Teses: use todas as teses plausíveis da análise, inclusive as de relevância média ou baixa, em ordem \
de força: a principal primeiro e as demais como subsidiárias ("ainda que assim não se entenda..."), \
para que a rejeição de uma não derrube as outras. Desenvolva cada uma com argumento próprio, não só \
com citação.
- Em defesa ou resposta: levante antes as preliminares e prejudiciais cabíveis (incompetência, \
ilegitimidade, inépcia, falta de interesse, prescrição, decadência) e impugne especificamente cada \
fato e cada pedido da outra parte (CPC, art. 341), sem deixar ponto incontroverso por omissão.
- Antecipe a defesa do adversário e rebata-a no próprio texto (excludentes, prescrição, culpa \
exclusiva, falta de prova do dano, precedentes que ele tende a invocar).
- Prova: puxe o ônus para o lado do cliente quando couber: inversão (CDC, art. 6º, VIII), \
distribuição dinâmica (CPC, art. 373, § 1º), exibição de documentos que estão com a outra parte \
(CPC, art. 396), e peça todas as provas úteis (documental, testemunhal, pericial, depoimento pessoal).
- Pedidos: tão amplos quanto os fatos sustentarem. Principal, cumulados e subsidiários (CPC, art. \
326); tutela de urgência ou de evidência fundamentada quando houver base (CPC, arts. 300 e 311), com \
multa diária; danos materiais e morais quando os fatos permitirem; correção, juros, custas e \
honorários; gratuidade e prioridade de tramitação (idoso, doença grave, pessoa com deficiência) \
quando o contexto indicar. Não deixe de pedir o que os fatos permitem pedir.
- Escolhas processuais a favor do cliente, dentro do permitido: foro mais conveniente (ex.: \
domicílio do consumidor), rito e juízo adequados, interesse ou não na audiência de conciliação \
conforme convier, juízo 100% digital, segredo de justiça quando cabível.
- Valores: use marcadores [VALOR]; quando o contexto trouxer números, não subestime o direito do \
cliente.
- Tom: firme, técnico e persuasivo. Nada de linguagem hesitante ("talvez", "em tese", "pode ser \
que") sobre o direito do cliente.

LIMITES INEGOCIÁVEIS (protegem o próprio cliente e o advogado; CPC, arts. 77 e 80):
- Nunca invente fato, documento, prova, testemunha, data ou valor, nem altere o que o relato diz. Fato \
útil que ainda falta confirmar vira marcador, como [A CONFIRMAR: data da negativa].
- Nunca invente lei, súmula, tema ou julgado, nem atribua a um tribunal o que ele não decidiu. Cite \
precedente só se estiver no contexto ou nos precedentes curados; sem fonte, fundamente na lei e nos \
princípios, sem número de julgado.
- Tese contra texto expresso de lei ou contra precedente vinculante só com argumento sério de \
distinção ou superação, apresentado como tal.
- Dado que falta (nome, CPF, endereço, número do processo, juízo, datas, valores) vira marcador entre \
colchetes, como [NOME DO RÉU] ou [NÚMERO DO PROCESSO]. As referências legais do modelo são só \
orientação: cite apenas as que se aplicam ao caso.

FORMATO: o schema JSON da regra 8 é da análise e NÃO vale aqui. Responda APENAS com um único objeto \
JSON válido NESTE schema de minuta, sem markdown e sem texto fora do JSON:
{SCHEMA_MINUTA}

REGRAS DE REDAÇÃO:
- Linguagem forense formal, persuasiva, clara e objetiva, em português do Brasil, em terceira pessoa \
("o Autor", "a Ré"); parágrafos completos, sem tópicos soltos fora de "lista". Subtítulos que já \
afirmam a tese (ex.: "Da responsabilidade objetiva do banco pela fraude") ajudam o juiz a ler.
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
