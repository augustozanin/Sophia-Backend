"""
Catálogo curado de precedentes por área, para a análise, o chat e a minuta.

Cada precedente foi conferido em VERIFICADO_EM nos portais oficiais (STF, STJ, CJF/TNU, TRF4):
número, órgão, tese e situação. Quando só deu para conferir em fonte secundária, o item diz
isso no status ou no alerta. A seleção segue três níveis de autoridade:

- N1: vinculante nacional (STF em repercussão geral ou controle concentrado; STJ em repetitivo).
- N2: uniformização (TNU nos Juizados Especiais Federais; súmulas do STJ, CPC art. 927, IV).
- N3: regional da 4ª Região (TRF4, TRU4; TJs de RS, SC e PR). Vale só lá.

Status: VIGENTE | EM ATENÇÃO (embargos, mérito pendente, trânsito não conferido) | ALTERADO
(vale a versão nova descrita) | SUPERADO (só como alerta) | NÃO VERIFICADO (pista a confirmar).

Só as sub-áreas ligadas ao caso entram no prompt (palavras-chave no relato), no máximo
LIMITE_SUBAREAS, para caber no limite de tokens do provedor. Sem texto do caso, nada entra.

Para atualizar: reabra cada URL, confira a situação, ajuste o status e VERIFICADO_EM. Itens com
status EM ATENÇÃO são os primeiros a revisar.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List

VERIFICADO_EM = "15/11/2026"
LIMITE_SUBAREAS = 3
# Caracteres do bloco de precedentes por tarefa (~4 por token). A sub-área mais ligada ao caso
# sempre entra; as seguintes só se couberem. Protege o limite de tokens por minuto do Groq gratuito.
ORCAMENTO = {"analise": 9_000, "chat": 6_500, "minuta": 6_500}
STATUS = ("VIGENTE", "EM ATENÇÃO", "ALTERADO", "SUPERADO", "NÃO VERIFICADO")
NIVEIS = ("N1", "N2", "N3")


def _stj(n: int) -> str:
    return ("https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?novaConsulta=true"
            f"&tipo_pesquisa=T&cod_tema_inicial={n}&cod_tema_final={n}")


def _stf(n: int) -> str:
    return f"https://portal.stf.jus.br/jurisprudenciaRepercussao/tema.asp?num={n}"


def _tnu_sumula(n: int) -> str:
    return f"https://www.cjf.jus.br/phpdoc/virtus/sumula.php?nsul={n}"


def _tnu_tema(n: int) -> str:
    return ("https://www.cjf.jus.br/cjf/corregedoria-da-justica-federal/turma-nacional-de-uniformizacao/"
            f"temas-representativos?tema={n}")


def _stj_sumula(n: int) -> str:
    return f"https://scon.stj.jus.br/SCON/sumstj/toc.jsp?sumula={n}"


_TRU4_SUMULAS = "https://www.trf4.jus.br/trf4/controlador.php?acao=sumulas_tru4"
_TRF4_SUMULAS = "https://www.trf4.jus.br/trf4/controlador.php?acao=sumulas_trf4"
_STF_ADI_7265 = ("https://noticias.stf.jus.br/postsnoticias/"
                 "stf-fixa-criterios-para-que-planos-de-saude-cubram-tratamentos-fora-da-lista-da-ans/")
_STF_INFO_1214 = "https://www.stf.jus.br/arquivo/informativo/documento/informativo1214.htm"


def _p(id: str, nivel: str, especie: str, status: str, motivo: str, titulo: str, fato: str,
       tese: str, busca: str, fonte: str, alerta: str = "") -> Dict[str, str]:
    return {"id": id, "nivel": nivel, "especie": especie, "status": status, "motivo": motivo,
            "titulo": titulo, "fato": fato, "tese": tese, "alerta": alerta, "busca": busca, "fonte": fonte}


def _sub(id: str, nome: str, palavras: List[str], precedentes: List[Dict[str, str]],
         lacunas: str = "") -> Dict[str, Any]:
    return {"id": id, "nome": nome, "palavras": palavras, "precedentes": precedentes, "lacunas": lacunas}


# ====================================================================== Previdenciário
_PREVIDENCIARIO = [
    _sub("acesso", "Requerimento ao INSS, prova nova e DER",
         [r"requeriment", r"indeferi", r"negou", r"negad", r"\bder\b", r"data de entrada", r"carta de exig",
          r"processo administrativo", r"meu inss", r"documento novo", r"reafirma"],
         [
             _p("STF, Tema 350 (RE 631.240)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 03/05/2017",
                "Prévio requerimento administrativo",
                "Ainda não pediu o benefício ao INSS e quer ir direto à Justiça.",
                "A ação de concessão exige pedido prévio ao INSS, mas não o esgotamento da via "
                "administrativa; o pedido é dispensável quando o entendimento do INSS é notoriamente "
                "contrário à pretensão.",
                '"Tema 350" STF "prévio requerimento administrativo" "RE 631240"', _stf(350),
                "Para revisão e restabelecimento, confira as exceções no acórdão antes de dispensar o pedido."),
             _p("STJ, Tema 1124", "N1", "tese repetitiva, nacional", "EM ATENÇÃO",
                "julgado em 08/10/2025, acórdão de 06/11/2025, embargos em 09/2026, sem trânsito em julgado",
                "Prova não levada ao INSS: interesse de agir e início do benefício",
                "O INSS negou por falta de documento e agora o cliente conseguiu o PPP, laudo ou outro papel.",
                "O requerimento deve ser apto. Documento ou fato novo exige novo pedido ao INSS, sob pena de "
                "extinção sem mérito (salvo prova só complementar). Mesmas provas do processo administrativo: "
                "DIB na DER. INSS não pediu complementação: DIB pode ser a DER. Prova surgida depois do "
                "ajuizamento ou impossível antes: DIB na citação.",
                '"Tema 1124" STJ "efeitos financeiros" "prova não submetida" INSS', _stj(1124)),
             _p("STJ, Tema 995", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Reafirmação da DER no curso da ação",
                "Quando pediu, faltava pouco tempo de contribuição, mas continuou trabalhando depois.",
                "Pode-se reafirmar a DER para quando os requisitos se completaram, mesmo depois do "
                "ajuizamento, até a decisão nas instâncias ordinárias (CPC, arts. 493 e 933), observada a "
                "causa de pedir.",
                '"Tema 995" STJ "reafirmação da DER"', _stj(995)),
         ], lacunas="N2 e N3: sem precedente verificado."),
    _sub("especial", "Tempo especial: EPI, ruído e PPP",
         [r"especial", r"insalubr", r"ruido", r"barulho", r"\bepis?\b", r"protetor", r"\bppp\b", r"ltcat",
          r"agente[s]? nociv", r"quimic", r"poeira", r"calor", r"metalurg", r"frigorif"],
         [
             _p("STF, Tema 555 (ARE 664.335)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 04/03/2015",
                "EPI e tempo especial; regra própria do ruído",
                "A empresa dava EPI ou protetor, mas o ambiente era muito barulhento ou tinha agentes nocivos.",
                "Se o EPI neutraliza de fato a nocividade, não há tempo especial. Para ruído acima do limite "
                "de tolerância, a declaração de EPI eficaz no PPP não afasta a especialidade.",
                '"Tema 555" STF "ARE 664335" EPI ruído', _stf(555)),
             _p("STJ, Tema 1090", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "EPI eficaz no PPP: presunção e ônus da prova",
                'O INSS não reconheceu o período porque o PPP marca "EPI eficaz".',
                "A informação de EPI no PPP descaracteriza, em princípio, o tempo especial, salvo hipóteses "
                "excepcionais. O segurado deve provar a ineficácia (inadequação ao risco, certificado "
                "irregular, falta de manutenção, troca ou treinamento). Havendo dúvida ou divergência, "
                "decide-se a favor do segurado.",
                '"Tema 1090" STJ EPI PPP "ônus" segurado', _stj(1090),
                "Para ruído, prevalece o Tema 555/STF."),
             _p("STJ, Tema 1083", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Ruído variável: NEN ou pico",
                "O barulho mudava ao longo do dia e o PPP traz vários níveis de ruído.",
                "Com níveis diferentes de ruído, afere-se pelo Nível de Exposição Normalizado (NEN). Sem essa "
                "informação, usa-se o pico, desde que perícia judicial comprove exposição habitual e permanente.",
                '"Tema 1083" STJ ruído "Nível de Exposição Normalizado"', _stj(1083)),
             _p("TNU, Tema 174", "N2", "tese de uniformização, Juizados Especiais Federais", "VIGENTE", "julgado",
                "Metodologia do ruído no PPP",
                "O PPP informa o ruído, mas não diz como foi medido.",
                "Desde 19/11/2003, o ruído contínuo ou intermitente deve ser medido pela NHO-01 (Fundacentro) "
                "ou pela NR-15, refletindo toda a jornada, com a técnica indicada no PPP. Se o PPP for omisso "
                "ou duvidoso, junte o LTCAT.",
                '"Tema 174" TNU ruído "NHO-01" PPP metodologia', _tnu_tema(174)),
             _p("TRF4, IRDR Tema 15", "N3", "IRDR, só na 4ª Região", "NÃO VERIFICADO",
                "texto oficial não aberto; existência confirmada na página do Tema 1090/STJ",
                "EPI: prova da ineficácia na 4ª Região",
                'O PPP diz "EPI eficaz", e o cliente trabalhou no RS, SC ou PR.',
                "Segundo fontes secundárias, admite prova da ineficácia do EPI e afasta o EPI em hipóteses como "
                "ruído e agentes cancerígenos.",
                '"IRDR 15" TRF4 EPI "Tema 1090"', _stj(1090),
                "O Tema 1090/STJ (N1) prevalece. Não cite o número sem conferir a tese."),
         ]),
    _sub("aposentadoria-especial", "Aposentadoria especial: vigilante e volta à atividade nociva",
         [r"vigilant", r"\bvigia\b", r"seguranca patrimonial", r"arma de fogo", r"aposentadoria especial",
          r"continu\w* trabalhando", r"volt\w* a trabalhar"],
         [
             _p("STF, Tema 1209 (RE 1.368.225)", "N1", "tese de repercussão geral, nacional", "EM ATENÇÃO",
                "acórdão de mérito publicado em 04/03/2026, sem trânsito em julgado",
                "Vigilante não é atividade especial por periculosidade",
                "Trabalhou anos como vigilante, armado ou não, e quer contar o tempo como especial.",
                "A atividade de vigilante, com ou sem arma de fogo, não se caracteriza como especial para a "
                "aposentadoria do art. 201, § 1º, da Constituição.",
                '"Tema 1209" STF vigilante "atividade especial"', _stf(1209),
                "Há decisões que discutem períodos anteriores a 1997 e exposição a outros agentes. A Súmula 10 "
                "da TRU4 (vigilante armado equiparado a guarda) conflita com o tema, que prevalece."),
             _p("STF, Tema 709 (RE 791.961)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 01/12/2021",
                "Aposentado especial que continua em atividade nociva",
                "Aposentou-se pela especial e continua ou voltou a trabalhar no mesmo ambiente.",
                "É constitucional vedar a aposentadoria especial a quem permanece ou retorna à atividade "
                "nociva. A DIB é a DER, mas, implantado o benefício, a continuidade faz cessar o pagamento, sem "
                "cancelar o benefício.",
                '"Tema 709" STF "aposentadoria especial" atividade nociva', _stf(709),
                "Modulação: preservadas decisões transitadas e valores recebidos de boa-fé até 23/02/2021."),
         ], lacunas="N2 e N3: sem precedente verificado além do conflito registrado."),
    _sub("incapacidade", "Benefícios por incapacidade e auxílio-acidente",
         [r"auxilio[- ]doenca", r"incapacidad", r"invalidez", r"afastad", r"afastamento", r"pericia",
          r"\balta\b", r"acidente", r"sequela", r"auxilio[- ]acidente", r"lesao", r"nao consig\w* trabalhar",
          r"encostad"],
         [
             _p("STJ, Tema 1013", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Trabalhou enquanto esperava o benefício",
                "O INSS negou o auxílio e o cliente continuou trabalhando doente até a Justiça decidir.",
                "Entre o indeferimento e a implantação judicial do auxílio-doença ou da aposentadoria por "
                "invalidez, o segurado recebe juntos os salários do período e o benefício retroativo, ainda que "
                "o trabalho fosse incompatível com a incapacidade.",
                '"Tema 1013" STJ "recebimento conjunto" incapacidade', _stj(1013)),
             _p("STJ, Tema 862", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Início do auxílio-acidente",
                "Ficou com sequela; o auxílio-doença acabou e não recebeu mais nada.",
                "O auxílio-acidente começa no dia seguinte à cessação do auxílio-doença que lhe deu origem "
                "(Lei 8.213/1991, art. 86, § 2º), respeitada a prescrição de cinco anos (Súmula 85/STJ).",
                '"Tema 862" STJ "auxílio-acidente" "termo inicial"', _stj(862)),
             _p("STF, Tema 1125 (RE 1.298.832)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 20/09/2023",
                "Auxílio-doença conta como carência se intercalado",
                "Ficou um tempo afastado pelo INSS e depois voltou a trabalhar; quer saber se esse tempo conta.",
                "É constitucional contar, para carência, o período em auxílio-doença, desde que intercalado "
                "com períodos de atividade.",
                '"Tema 1125" STF carência "auxílio-doença" intercalado', _stf(1125)),
             _p("TNU, Súmula 47", "N2", "súmula da TNU, Juizados Especiais Federais", "VIGENTE",
                "enunciado conferido no CJF",
                "Incapacidade parcial e condições pessoais",
                "O perito disse que pode fazer serviço leve, mas o cliente tem idade, pouca instrução e só "
                "sabe trabalhar braçal.",
                "Reconhecida a incapacidade parcial, o juiz deve analisar as condições pessoais e sociais do "
                "segurado para a concessão de aposentadoria por invalidez.",
                '"Súmula 47" TNU incapacidade parcial condições pessoais', _tnu_sumula(47)),
             _p("TNU, Tema 277", "N2", "tese de uniformização, Juizados Especiais Federais", "VIGENTE",
                "trânsito em julgado em 25/04/2022",
                "Alta programada exige pedido de prorrogação",
                "O benefício acabou na data marcada pelo INSS e o cliente não pediu prorrogação.",
                "Para continuar o benefício com DCB estimada, o segurado precisa ter pedido prorrogação "
                "(Lei 8.213/1991, art. 60, § 9º), recurso ou reconsideração, quando previstos; sem isso, não "
                "há interesse de agir.",
                '"Tema 277" TNU "alta programada" prorrogação', _tnu_tema(277)),
             _p("TRU4, Súmula 7", "N3", "súmula regional, Juizados Federais da 4ª Região", "EM ATENÇÃO",
                "anterior ao Tema 1125/STF, que acrescentou a exigência de intercalação",
                "Benefício por incapacidade como carência (4ª Região)",
                "Recebeu benefício por incapacidade e quer contar o período como carência.",
                "Computa-se para carência o período em que o segurado recebeu benefício por incapacidade.",
                '"Súmula 7" TRU4 carência incapacidade', _TRU4_SUMULAS,
                "Aplique com a ressalva do Tema 1125/STF (N1): só se intercalado com atividade."),
         ]),
    _sub("bpc", "BPC/LOAS",
         [r"\bbpc\b", r"\bloas\b", r"beneficio assistencial", r"assistencial", r"deficien", r"idos[oa]",
          r"65 anos", r"cadunico", r"miserab", r"autis", r"\btea\b", r"baixa renda", r"renda per capita"],
         [
             _p("STF, Tema 27 (RE 567.985)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 11/12/2013",
                "Renda de 1/4 do salário mínimo não é critério único",
                "O INSS negou porque a renda da casa passa um pouco de 1/4 do salário mínimo por pessoa.",
                "O critério de renda per capita inferior a 1/4 do salário mínimo (LOAS, art. 20, § 3º) não é "
                "o único meio de aferir a miserabilidade, que pode ser provada por outros elementos do caso.",
                '"Tema 27" STF "RE 567985" miserabilidade', _stf(27),
                "A Lei 15.077/2024 alterou o art. 20 da LOAS (biometria, soma dos rendimentos do grupo "
                "familiar); confira o texto vigente."),
             _p("STF, Tema 312 (RE 580.963)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 13/02/2014",
                "Benefício de um salário mínimo de outro membro fica fora da renda",
                "Alguém da casa recebe aposentadoria ou BPC de um salário mínimo e o INSS somou na renda.",
                "É inconstitucional, por omissão parcial, o art. 34, parágrafo único, do Estatuto do Idoso: "
                "benefício de um salário mínimo de idoso ou pessoa com deficiência do grupo familiar também "
                "deve ser excluído do cálculo da renda per capita.",
                '"Tema 312" STF "RE 580963" renda per capita', _stf(312)),
             _p("STJ, Tema 185", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Miserabilidade por outros meios de prova",
                "A renda declarada não reflete as despesas reais da família (remédios, aluguel, cuidados).",
                "Renda per capita inferior a 1/4 do salário mínimo gera presunção absoluta de miserabilidade; "
                "acima disso, ela pode ser demonstrada por outros meios de prova.",
                '"Tema 185" STJ "benefício assistencial" "outros meios"', _stj(185)),
             _p("TNU, Súmula 80", "N2", "súmula da TNU, Juizados Especiais Federais", "VIGENTE",
                "enunciado conferido no CJF",
                "Avaliação social no BPC da pessoa com deficiência",
                "O pedido de BPC por deficiência foi analisado só com perícia médica.",
                "Após a Lei 12.470/2011, o BPC da pessoa com deficiência exige avaliação social por assistente "
                "social, ou outra providência que revele as condições reais de vida do requerente.",
                '"Súmula 80" TNU "avaliação social" LOAS', _tnu_sumula(80)),
         ], lacunas="N3: sem precedente verificado (a Súmula 6 da TRU4 sobre renda foi cancelada)."),
    _sub("pensao", "Pensão por morte e dependentes",
         [r"pensao", r"obito", r"falece", r"falecid", r"\bmorte\b", r"viuv", r"companheir", r"uniao estavel",
          r"dependent", r"amante", r"concubin", r"segunda familia"],
         [
             _p("STF, Tema 529 (RE 1.045.273)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 29/05/2021",
                "Uniões simultâneas não dividem a pensão",
                "O falecido era casado ou vivia com outra pessoa e mantinha também a relação com a cliente.",
                "Casamento ou união estável preexistente impede reconhecer outra união concomitante, inclusive "
                "para fins previdenciários, pelo dever de fidelidade e pela monogamia.",
                '"Tema 529" STF uniões concomitantes pensão', _stf(529),
                "Separação de fato do primeiro vínculo muda a análise; confira os fatos."),
             _p("STF, Tema 526 (RE 883.168)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 02/04/2022",
                "Concubinato com pessoa casada não gera pensão",
                "Manteve por anos relação com pessoa casada que não se separou.",
                "É incompatível com a Constituição reconhecer pensão por morte a quem manteve, por longo "
                "período e com aparência familiar, união com pessoa casada.",
                '"Tema 526" STF concubinato pensão', _stf(526)),
             _p("TNU, Súmula 63", "N2", "súmula da TNU, Juizados Especiais Federais", "ALTERADO",
                "enunciado alterado em 18/09/2025",
                "Prova da união estável depende da data do óbito",
                "Viveram juntos por anos, mas não há documento, só testemunhas.",
                "Para óbitos até a MP 871/2019, a união estável pode ser provada sem início de prova material. "
                "Para óbitos posteriores, vale a exigência legal de início de prova material contemporânea "
                "(Lei 8.213/1991, art. 16, § 5º; confira o texto).",
                '"Súmula 63" TNU "união estável" "MP 871"', _tnu_sumula(63)),
             _p("TRF4, Súmula 104", "N3", "súmula regional, TRF4", "EM ATENÇÃO",
                "editada em 2016, antes da MP 871/2019",
                "Prova testemunhal da união estável (4ª Região)",
                "Só há testemunhas da convivência, e o caso tramita no RS, SC ou PR.",
                "A legislação previdenciária não restringe a prova testemunhal para comprovar união estável.",
                '"Súmula 104" TRF4 "união estável" testemunhal', _TRF4_SUMULAS,
                "Use só para óbitos anteriores à MP 871/2019 (veja a Súmula 63 da TNU alterada)."),
         ]),
    _sub("rural", "Rural, segurado especial e aposentadoria híbrida",
         [r"\brural", r"\broca\b", r"lavoura", r"agricultor", r"boia[- ]fria", r"safrista", r"\bsitio\b",
          r"chacara", r"\bcolon[oa]", r"pescador", r"segurado especial", r"hibrida", r"produtor rural",
          r"bloco de produtor", r"\bitr\b"],
         [
             _p("STJ, Tema 554", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Boia-fria e início de prova material",
                "Trabalhou na roça como diarista ou boia-fria, sem carteira, e tem poucos papéis.",
                "Aplica-se a Súmula 149/STJ ao boia-fria: só testemunhas não bastam, é preciso início de prova "
                "material. Prova material de só parte do período, ampliada por testemunhas robustas, basta.",
                '"Tema 554" STJ "boia-fria" "Súmula 149"', _stj(554),
                "Tema 638/STJ (Súmula 577): dá para reconhecer tempo anterior ao documento mais antigo, com "
                "prova testemunhal convincente."),
             _p("STJ, Tema 642", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado em 08/09/2016",
                "Segurado especial deve estar no campo ao completar a idade",
                "Trabalhou na roça a vida toda, mas há alguns anos mudou para a cidade.",
                "Para a aposentadoria por idade rural, o segurado especial deve estar no campo quando completa "
                "a idade, ressalvado o direito adquirido de quem já reunia antes idade e carência.",
                '"Tema 642" STJ segurado especial "período imediatamente anterior"', _stj(642),
                "Se já não está no campo, avalie a aposentadoria híbrida (Tema 1007/STJ)."),
             _p("STJ, Tema 1007", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Aposentadoria híbrida com tempo rural antigo",
                "Trabalhou na roça quando jovem, antes de 1991, e depois na cidade com carteira.",
                "Tempo rural, ainda que remoto e descontínuo, anterior à Lei 8.213/1991, conta para a carência "
                "da aposentadoria híbrida por idade, sem recolhimentos, qualquer que seja o trabalho "
                "predominante ou o exercido ao completar a idade.",
                '"Tema 1007" STJ "aposentadoria híbrida" "rural remoto"', _stj(1007)),
             _p("TNU, Súmula 14", "N2", "súmula da TNU, Juizados Especiais Federais", "VIGENTE",
                "enunciado conferido no CJF",
                "Prova material não precisa cobrir toda a carência",
                "Tem documentos rurais de alguns anos, não de todo o período.",
                "Na aposentadoria rural por idade, o início de prova material não precisa corresponder a todo "
                "o período de carência.",
                '"Súmula 14" TNU "início de prova material" carência', _tnu_sumula(14)),
             _p("TNU, Súmula 34", "N2", "súmula da TNU, Juizados Especiais Federais", "VIGENTE",
                "enunciado conferido no CJF",
                "Prova material contemporânea",
                "Os documentos rurais foram feitos recentemente, sobre fatos antigos.",
                "Para comprovar labor rural, o início de prova material deve ser contemporâneo à época dos fatos.",
                '"Súmula 34" TNU contemporâneo rural', _tnu_sumula(34)),
             _p("TRU4, Súmula 9", "N3", "súmula regional, Juizados Federais da 4ª Região", "VIGENTE",
                "enunciado conferido no portal do TRF4",
                "Documentos em nome da família (4ª Região)",
                "Os documentos da roça estão no nome do pai, do marido ou de outro membro da família.",
                "Admitem-se como início de prova material documentos em nome de integrantes do grupo familiar "
                "em regime de economia familiar rural.",
                '"Súmula 9" TRU4 "economia familiar"', _TRU4_SUMULAS,
                "A Súmula 14 da TRU4 (boia-fria sem prova material) conflita com o Tema 554/STJ, que prevalece."),
         ]),
    _sub("revisoes", "Revisões, decadência e cálculo",
         [r"revis", r"recalcul", r"vida toda", r"decadenc", r"\brmi\b", r"valor da aposentadoria",
          r"aumentar a aposentadoria", r"calcul\w* errad"],
         [
             _p("STF, Tema 1102 (RE 1.276.977)", "N1", "tese de repercussão geral, nacional", "SUPERADO",
                "tese favorável cancelada após as ADIs 2.110 e 2.111; trânsito em julgado em 15/05/2026",
                "Revisão da vida toda não existe mais",
                "Ouviu falar da revisão da vida toda e quer pedir.",
                "As ADIs 2.110 e 2.111 validaram a regra de transição da Lei 9.876/1999 como obrigatória, e a "
                "tese de 2022 foi cancelada. O segurado não pode optar pela regra definitiva mais favorável.",
                '"Tema 1102" STF "vida toda" "ADI 2110"', _stf(1102),
                "Não use como fundamento. Fontes secundárias dizem que não há devolução do que foi recebido "
                "por decisões até 05/04/2024; confira no acórdão."),
             _p("STF, Tema 313 (RE 626.489)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 08/10/2014",
                "Decadência de 10 anos para revisar",
                "Aposentou-se há mais de 10 anos e acha que o cálculo saiu errado.",
                "Não há prazo decadencial para pedir a concessão inicial do benefício; para revisar benefício "
                "já concedido vale o prazo de 10 anos, inclusive para os concedidos antes da MP 1.523/1997.",
                '"Tema 313" STF decadência revisão "RE 626489"', _stf(313)),
             _p("STJ, Tema 975", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Decadência alcança o que o INSS não analisou",
                "Quer incluir na revisão um período que o INSS nem examinou na concessão.",
                "O prazo de 10 anos (Lei 8.213/1991, art. 103) vale também quando a questão não foi apreciada "
                "pelo INSS no ato de concessão.",
                '"Tema 975" STJ decadência "não apreciada"', _stj(975)),
         ], lacunas="N2 e N3: sem precedente verificado."),
]

# ====================================================================== Consumidor
_CONSUMIDOR = [
    _sub("fraudes-bancarias", "Bancos: fraude, golpe e contratação não reconhecida",
         [r"fraude", r"golpe", r"\bpix\b", r"falsa central", r"clonad", r"nao contratei", r"nao reconhec",
          r"no meu nome", r"assinatura", r"\brmc\b", r"\brcc\b", r"cartao consignado", r"margem consign",
          r"emprestimo"],
         [
             _p("STJ, Tema 466", "N1", "tese repetitiva, nacional (originou a Súmula 479/STJ)", "VIGENTE",
                "trânsito em julgado",
                "Fraude de terceiro é fortuito interno do banco",
                "Abriram conta ou fizeram empréstimo no nome do cliente, ou ele caiu num golpe e o banco não "
                "devolveu.",
                "Instituições financeiras respondem objetivamente pelos danos de fortuito interno ligados a "
                "fraudes e delitos de terceiros em operações bancárias.",
                '"Tema 466" STJ "fortuito interno" fraude banco', _stj(466),
                "Golpes por engenharia social (falsa central, Pix) são decididos caso a caso (falha de "
                "segurança do banco versus culpa exclusiva da vítima); não há tese repetitiva específica."),
             _p("STJ, Tema 1061", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Assinatura contestada: o banco prova",
                "O banco diz que o cliente assinou o contrato, mas a assinatura não é dele.",
                "Se o consumidor impugna a autenticidade da assinatura no contrato juntado pelo banco, cabe ao "
                "banco provar que é autêntica (CPC, arts. 6º, 369 e 429, II).",
                '"Tema 1061" STJ assinatura "ônus" banco', _stj(1061)),
             _p("STJ, Tema 1414", "N1", "tema repetitivo afetado, ainda sem tese", "EM ATENÇÃO",
                "afetado em 2026; sem julgamento; recursos especiais sobre o tema suspensos",
                "Cartão consignado (RMC/RCC): validade, abuso e prazo",
                "Achava que tinha feito empréstimo consignado, mas era cartão, e o desconto nunca acaba.",
                "Sem tese ainda. O STJ vai decidir se vale a decadência do art. 178 do Código Civil ou se há "
                "nulidade sem prazo, e fixar parâmetros objetivos de validade e de abuso. Absorveu o Tema 1328 "
                "(dano moral presumido), que foi cancelado.",
                '"Tema 1414" STJ "cartão de crédito consignado" RMC', _stj(1414),
                "Não afirme o resultado. A MP 1.355/2026 prevê a extinção gradual do RMC e do RCC no INSS "
                "(confira o texto oficial)."),
             _p("TJSC, IRDR Tema 26", "N3", "IRDR, só em Santa Catarina", "EM ATENÇÃO",
                "tese levada ao STJ (recurso especial em IRDR, hoje no Tema 1414)",
                "RMC anulado não gera dano moral presumido (SC)",
                "O contrato de cartão consignado foi anulado e o cliente quer dano moral.",
                "Segundo fontes secundárias, a invalidação do contrato de cartão com RMC não gera dano moral "
                "presumido.",
                '"IRDR 26" TJSC RMC "dano moral"', _stj(1328),
                "Pendente no STJ (Tema 1414). Não trate como definitivo."),
         ]),
    _sub("contratos-bancarios", "Contratos bancários: juros, descontos e atendimento",
         [r"juros", r"revisional", r"\btaxa", r"financiament", r"desconto", r"conta[- ]salario", r"salario",
          r"\bfila\b", r"espera", r"atendimento bancario", r"tarifa"],
         [
             _p("STJ, Tema 27 (REsp 1.061.530/RS)", "N1", "tese repetitiva, nacional", "VIGENTE",
                "trânsito em julgado em 13/05/2010",
                "Revisão de juros remuneratórios",
                "Os juros do empréstimo, do financiamento ou do cartão são altíssimos.",
                "A revisão dos juros remuneratórios só cabe em situações excepcionais, com relação de consumo "
                "e abusividade cabalmente demonstrada no caso concreto (CDC, art. 51, § 1º).",
                '"Tema 27" STJ "juros remuneratórios" abusividade "taxa média"', _stj(27),
                "A comparação com a taxa média do Banco Central para a operação é o parâmetro usual "
                "(orientação do mesmo julgamento, conferida em fontes secundárias)."),
             _p("STJ, Tema 1085", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Desconto de empréstimo comum na conta-salário",
                "O banco desconta da conta onde cai o salário quase tudo o que entra.",
                "São lícitos os descontos de empréstimos comuns em conta-corrente, mesmo a que recebe salário, "
                "se autorizados e enquanto durar a autorização; não se aplica por analogia o limite de 30% do "
                "consignado (Lei 10.820/2003).",
                '"Tema 1085" STJ desconto "conta-corrente" 30%', _stj(1085),
                "Em superendividamento, veja a sub-área própria."),
             _p("STJ, Tema 1156", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Demora no atendimento bancário",
                "Ficou mais tempo na fila do banco do que a lei municipal permite.",
                "O simples descumprimento do prazo legal para atendimento bancário não gera, por si só, dano "
                "moral presumido.",
                '"Tema 1156" STJ fila banco "dano moral"', _stj(1156)),
         ], lacunas="N2 e N3: sem precedente verificado."),
    _sub("superendividamento", "Superendividamento e mínimo existencial",
         [r"superendivid", r"minimo existencial", r"muitas dividas", r"nao consig\w* pagar", r"renegoci",
          r"repactua"],
         [
             _p("STF, ADPFs 1.005, 1.006 e 1.097", "N1", "controle concentrado, eficácia geral", "EM ATENÇÃO",
                "julgadas em 23/04/2026 (Informativo 1214); trânsito em julgado não conferido",
                "Mínimo existencial de R$ 600 e consignado",
                "O cliente tem várias dívidas e o que sobra do salário não paga o básico.",
                "É constitucional fixar por decreto o valor do mínimo existencial (Decreto 11.150/2022, "
                "R$ 600), com reavaliações periódicas baseadas em estudos técnicos. É inconstitucional excluir "
                "o crédito consignado do cálculo.",
                'ADPF 1005 1006 1097 "mínimo existencial" STF', _STF_INFO_1214,
                "Use com a Lei 14.181/2021 (CDC, arts. 104-A a 104-C)."),
         ], lacunas="N2 e N3: sem precedente verificado."),
    _sub("planos-de-saude", "Planos de saúde",
         [r"plano de saude", r"convenio", r"operadora", r"unimed", r"cobertura", r"\brol\b", r"\bans\b",
          r"cirurgia", r"tratamento", r"medicament", r"internac", r"mensalidade", r"faixa etaria",
          r"home care", r"terapia", r"bariatric", r"carencia", r"preexistent"],
         [
             _p("STF, ADI 7.265", "N1", "controle concentrado, eficácia geral", "VIGENTE",
                "julgada em 18/09/2025",
                "Cobertura fora do rol da ANS: cinco critérios cumulativos",
                "O plano negou porque o tratamento não está no rol da ANS.",
                "A Lei 14.454/2022 é válida com interpretação conforme: o plano cobre tratamento fora do rol se, "
                "ao mesmo tempo, (1) há prescrição do médico ou odontólogo assistente; (2) não houve negativa "
                "expressa nem há análise pendente na ANS; (3) não há alternativa adequada no rol; (4) há "
                "comprovação científica de eficácia e segurança; (5) há registro na Anvisa.",
                '"ADI 7265" STF rol ANS critérios', _STF_ADI_7265),
             _p("STJ, Tema 1082", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Cancelamento de plano coletivo durante tratamento",
                "A operadora cancelou o plano coletivo no meio de um tratamento grave.",
                "Mesmo após rescisão unilateral regular de plano coletivo, a operadora deve manter a assistência "
                "a quem está internado ou em tratamento que garanta a sobrevivência ou a incolumidade, até a "
                "alta, se o titular pagar integralmente a mensalidade.",
                '"Tema 1082" STJ cancelamento plano coletivo tratamento', _stj(1082)),
             _p("STJ, Tema 952", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Reajuste por faixa etária",
                "Mudou de faixa etária (por exemplo, aos 59 anos) e a mensalidade disparou.",
                "O reajuste por faixa etária em plano individual ou familiar é válido se previsto no contrato, "
                "conforme as normas da ANS e sem percentuais desarrazoados ou aleatórios, sem base atuarial, "
                "que onerem excessivamente ou discriminem o idoso.",
                '"Tema 952" STJ reajuste "faixa etária"', _stj(952),
                "Planos coletivos: o Tema 1016/STJ estende essas teses (sem CDC na autogestão) e define a "
                '"variação acumulada"; acórdão publicado, recurso extraordinário pendente.'),
             _p("STJ, Súmula 608", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor",
                "CDC nos planos de saúde, salvo autogestão",
                "Plano de empresa, sindicato ou associação que administra o próprio plano.",
                "Aplica-se o CDC aos contratos de plano de saúde, salvo os administrados por entidades de "
                "autogestão.",
                '"Súmula 608" STJ autogestão', _stj_sumula(608)),
             _p("STJ, Súmula 597", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor",
                "Carência em urgência e emergência",
                "Negaram atendimento de urgência porque o plano estava em carência.",
                "É abusiva a cláusula que prevê carência para urgência ou emergência acima de 24 horas da "
                "contratação.",
                '"Súmula 597" STJ carência urgência', _stj_sumula(597)),
         ], lacunas="N3: sem precedente verificado."),
    _sub("negativacao-cobranca", "Negativação e cobrança indevida",
         [r"negativ", r"serasa", r"\bspc\b", r"nome sujo", r"cadastro", r"protest", r"cobranc\w* indevid",
          r"cobrara?m", r"nao devo", r"em dobro", r"devolu", r"fatura", r"conta de luz", r"telefon"],
         [
             _p("STJ, Tema 929", "N1", "tese repetitiva, nacional", "EM ATENÇÃO",
                "julgado em 15/09/2026, acórdão publicado em 03/11/2026, sem trânsito em julgado",
                "Devolução em dobro (CDC, art. 42)",
                "Cobraram algo que o cliente não devia, e ele pagou.",
                "A devolução em dobro independe de má-fé e cabe quando a cobrança contraria a boa-fé objetiva. "
                "Recusa ou omissão do fornecedor diante de reclamação prévia é indício suficiente. O fornecedor "
                "deve provar que não agiu de forma desleal ou descuidada. Divergência jurisprudencial ou "
                "cláusula depois anulada configuram engano justificável.",
                '"Tema 929" STJ "repetição em dobro" "boa-fé objetiva"', _stj(929),
                "Só sobre o que foi efetivamente pago. Confira se o acórdão manteve a modulação temporal da "
                "Corte Especial (EAREsp 676.608/RS). Fraude que levou à negativação: Tema 466/STJ."),
             _p("STJ, Súmula 385", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor",
                "Negativação indevida com anotação anterior legítima",
                "Foi negativado por dívida que não é dele, mas já tinha outro apontamento legítimo.",
                "Havendo inscrição legítima anterior, a anotação irregular não gera dano moral, ressalvado o "
                "direito ao cancelamento.",
                '"Súmula 385" STJ "inscrição legítima"', _stj_sumula(385)),
         ], lacunas="N3: sem precedente verificado."),
    _sub("transporte-aereo", "Transporte aéreo",
         [r"\bvoo", r"aere[oa]", r"companhia aerea", r"atras", r"cancelad", r"bagagem", r"\bmala\b",
          r"extravi", r"overbooking", r"embarque", r"conexao", r"passagem", r"aeroporto"],
         [
             _p("STF, Tema 210 (RE 636.331)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 13/12/2022",
                "Voo internacional: danos materiais pelas convenções",
                "A mala sumiu ou houve prejuízo material num voo internacional.",
                "Pelo art. 178 da Constituição, as Convenções de Varsóvia e de Montreal, que limitam a "
                "responsabilidade das transportadoras, prevalecem sobre o CDC quanto aos danos materiais.",
                '"Tema 210" STF Montreal "danos materiais"', _stf(210)),
             _p("STF, Tema 1240 (RE 1.394.401)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 05/08/2023",
                "Voo internacional: dano moral fora das convenções",
                "Teve transtorno grave num voo internacional e quer dano moral.",
                "As Convenções de Varsóvia e de Montreal não se aplicam aos danos extrapatrimoniais do "
                "transporte aéreo internacional, que seguem o CDC.",
                '"Tema 1240" STF "danos extrapatrimoniais" Montreal', _stf(1240)),
             _p("STF, Tema 1417 (ARE 1.560.244)", "N1", "repercussão geral reconhecida, mérito pendente",
                "EM ATENÇÃO", "acórdão de repercussão geral publicado em 29/08/2025; sem tese de mérito",
                "Atraso ou cancelamento por caso fortuito ou força maior: CBA ou CDC",
                "O voo foi cancelado ou atrasou por mau tempo ou problema alheio à companhia.",
                "Sem tese ainda. O STF vai decidir se as normas do transporte aéreo prevalecem sobre o CDC na "
                "responsabilidade por cancelamento, alteração ou atraso de voo por caso fortuito ou força maior.",
                '"Tema 1417" STF atraso voo "força maior"', _stf(1417),
                "Há notícia de suspensão nacional dos processos; confira antes de ajuizar. Dano moral por "
                "atraso, em regra, não é presumido (CBA, art. 251-A; orientação de turmas do STJ, não tese "
                "vinculante)."),
         ], lacunas="N2 e N3: sem precedente verificado."),
]

CATALOGO: Dict[str, List[Dict[str, Any]]] = {
    "previdenciario": _PREVIDENCIARIO,
    "consumidor": _CONSUMIDOR,
}

_ALCANCE_REGIONAL = {
    "previdenciario": "regional da 4ª Região: RS, SC e PR, só para casos que tramitam lá",
    "consumidor": "regional do TJ indicado (RS, SC ou PR), só para casos que tramitam lá",
}

_CABECALHO = """\
PRECEDENTES CURADOS DESTA ÁREA (pesquisa da equipe Sophia; situação conferida em {data} nos portais \
oficiais e sujeita a mudança depois disso). Entram só as sub-áreas ligadas aos fatos. São PONTO DE \
PARTIDA, NÃO LISTA FECHADA: considere também outras teses aplicáveis a estes fatos, ainda que fora \
desta lista. Como usar:
- Use um precedente só se o fato-tipo corresponder ao relato. Não force.
- VIGENTE: pode fundamentar. Em "fonte", escreva o identificador e a URL indicada.
- EM ATENÇÃO: use com a ressalva do motivo e status "em_analise".
- ALTERADO: aplique só a versão atual descrita.
- SUPERADO: nunca como fundamento favorável; só como alerta, dizendo por quê.
- NÃO VERIFICADO: não cite o número; é pista a confirmar.
- N1 (vinculante nacional) prevalece sobre N2 (uniformização) e N3 ({alcance}). Diga se é tese, \
súmula ou IRDR: não são a mesma coisa.
- Precedente fora desta lista continua sujeito às regras 1 e 2."""

_EXTRA_POR_TAREFA = {
    "analise": ("- Com busca na web ativa: pesquise cada precedente que usar (a \"Busca\" indicada ajuda) para "
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
    partes = [_CABECALHO.format(data=VERIFICADO_EM, alcance=_ALCANCE_REGIONAL.get(area_id, "regional"))]
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
