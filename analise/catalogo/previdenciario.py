"""Direito Previdenciário: precedentes curados (conferidos em 15/11/2026: STF, STJ, CJF/TNU e TRF4/TRU4).

Níveis nesta área: N1 = STF (repercussão geral) e STJ (repetitivos); N2 = TNU (súmulas e temas, nos Juizados
Especiais Federais); N3 = TRF4 e TRU4 (4ª Região)."""
from .base import p, stf, stj, sub, tnu_sumula, tnu_tema

VERIFICADO = "15/11/2026"
ALCANCE = "regional da 4ª Região: RS, SC e PR, só para casos que tramitam lá"

TRU4_SUMULAS = "https://www.trf4.jus.br/trf4/controlador.php?acao=sumulas_tru4"
TRF4_SUMULAS = "https://www.trf4.jus.br/trf4/controlador.php?acao=sumulas_trf4"

SUBAREAS = [
    sub("acesso", "Requerimento ao INSS, prova nova e DER",
         [r"requeriment", r"indeferi", r"negou", r"negad", r"\bder\b", r"data de entrada", r"carta de exig",
          r"processo administrativo", r"meu inss", r"documento novo", r"reafirma"],
         [
             p("STF, Tema 350 (RE 631.240)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 03/05/2017",
                "Prévio requerimento administrativo",
                "Ainda não pediu o benefício ao INSS e quer ir direto à Justiça.",
                "A ação de concessão exige pedido prévio ao INSS, mas não o esgotamento da via "
                "administrativa; o pedido é dispensável quando o entendimento do INSS é notoriamente "
                "contrário à pretensão.",
                '"Tema 350" STF "prévio requerimento administrativo" "RE 631240"', stf(350),
                "Para revisão e restabelecimento, confira as exceções no acórdão antes de dispensar o pedido."),
             p("STJ, Tema 1124", "N1", "tese repetitiva, nacional", "EM ATENÇÃO",
                "julgado em 08/10/2025, acórdão de 06/11/2025, embargos em 09/2026, sem trânsito em julgado",
                "Prova não levada ao INSS: interesse de agir e início do benefício",
                "O INSS negou por falta de documento e agora o cliente conseguiu o PPP, laudo ou outro papel.",
                "O requerimento deve ser apto. Documento ou fato novo exige novo pedido ao INSS, sob pena de "
                "extinção sem mérito (salvo prova só complementar). Mesmas provas do processo administrativo: "
                "DIB na DER. INSS não pediu complementação: DIB pode ser a DER. Prova surgida depois do "
                "ajuizamento ou impossível antes: DIB na citação.",
                '"Tema 1124" STJ "efeitos financeiros" "prova não submetida" INSS', stj(1124)),
             p("STJ, Tema 995", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Reafirmação da DER no curso da ação",
                "Quando pediu, faltava pouco tempo de contribuição, mas continuou trabalhando depois.",
                "Pode-se reafirmar a DER para quando os requisitos se completaram, mesmo depois do "
                "ajuizamento, até a decisão nas instâncias ordinárias (CPC, arts. 493 e 933), observada a "
                "causa de pedir.",
                '"Tema 995" STJ "reafirmação da DER"', stj(995)),
         ], lacunas="N2 e N3: sem precedente verificado."),
    sub("especial", "Tempo especial: EPI, ruído e PPP",
         [r"especial", r"insalubr", r"ruido", r"barulho", r"\bepis?\b", r"protetor", r"\bppp\b", r"ltcat",
          r"agente[s]? nociv", r"quimic", r"poeira", r"calor", r"metalurg", r"frigorif"],
         [
             p("STF, Tema 555 (ARE 664.335)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 04/03/2015",
                "EPI e tempo especial; regra própria do ruído",
                "A empresa dava EPI ou protetor, mas o ambiente era muito barulhento ou tinha agentes nocivos.",
                "Se o EPI neutraliza de fato a nocividade, não há tempo especial. Para ruído acima do limite "
                "de tolerância, a declaração de EPI eficaz no PPP não afasta a especialidade.",
                '"Tema 555" STF "ARE 664335" EPI ruído', stf(555)),
             p("STJ, Tema 1090", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "EPI eficaz no PPP: presunção e ônus da prova",
                'O INSS não reconheceu o período porque o PPP marca "EPI eficaz".',
                "A informação de EPI no PPP descaracteriza, em princípio, o tempo especial, salvo hipóteses "
                "excepcionais. O segurado deve provar a ineficácia (inadequação ao risco, certificado "
                "irregular, falta de manutenção, troca ou treinamento). Havendo dúvida ou divergência, "
                "decide-se a favor do segurado.",
                '"Tema 1090" STJ EPI PPP "ônus" segurado', stj(1090),
                "Para ruído, prevalece o Tema 555/STF."),
             p("STJ, Tema 1083", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Ruído variável: NEN ou pico",
                "O barulho mudava ao longo do dia e o PPP traz vários níveis de ruído.",
                "Com níveis diferentes de ruído, afere-se pelo Nível de Exposição Normalizado (NEN). Sem essa "
                "informação, usa-se o pico, desde que perícia judicial comprove exposição habitual e permanente.",
                '"Tema 1083" STJ ruído "Nível de Exposição Normalizado"', stj(1083)),
             p("TNU, Tema 174", "N2", "tese de uniformização, Juizados Especiais Federais", "VIGENTE", "julgado",
                "Metodologia do ruído no PPP",
                "O PPP informa o ruído, mas não diz como foi medido.",
                "Desde 19/11/2003, o ruído contínuo ou intermitente deve ser medido pela NHO-01 (Fundacentro) "
                "ou pela NR-15, refletindo toda a jornada, com a técnica indicada no PPP. Se o PPP for omisso "
                "ou duvidoso, junte o LTCAT.",
                '"Tema 174" TNU ruído "NHO-01" PPP metodologia', tnu_tema(174)),
             p("TRF4, IRDR Tema 15", "N3", "IRDR, só na 4ª Região", "NÃO VERIFICADO",
                "texto oficial não aberto; existência confirmada na página do Tema 1090/STJ",
                "EPI: prova da ineficácia na 4ª Região",
                'O PPP diz "EPI eficaz", e o cliente trabalhou no RS, SC ou PR.',
                "Segundo fontes secundárias, admite prova da ineficácia do EPI e afasta o EPI em hipóteses como "
                "ruído e agentes cancerígenos.",
                '"IRDR 15" TRF4 EPI "Tema 1090"', stj(1090),
                "O Tema 1090/STJ (N1) prevalece. Não cite o número sem conferir a tese."),
         ]),
    sub("aposentadoria-especial", "Aposentadoria especial: vigilante e volta à atividade nociva",
         [r"vigilant", r"\bvigia\b", r"seguranca patrimonial", r"arma de fogo", r"aposentadoria especial",
          r"continu\w* trabalhando", r"volt\w* a trabalhar"],
         [
             p("STF, Tema 1209 (RE 1.368.225)", "N1", "tese de repercussão geral, nacional", "EM ATENÇÃO",
                "acórdão de mérito publicado em 04/03/2026, sem trânsito em julgado",
                "Vigilante não é atividade especial por periculosidade",
                "Trabalhou anos como vigilante, armado ou não, e quer contar o tempo como especial.",
                "A atividade de vigilante, com ou sem arma de fogo, não se caracteriza como especial para a "
                "aposentadoria do art. 201, § 1º, da Constituição.",
                '"Tema 1209" STF vigilante "atividade especial"', stf(1209),
                "Há decisões que discutem períodos anteriores a 1997 e exposição a outros agentes. A Súmula 10 "
                "da TRU4 (vigilante armado equiparado a guarda) conflita com o tema, que prevalece."),
             p("STF, Tema 709 (RE 791.961)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 01/12/2021",
                "Aposentado especial que continua em atividade nociva",
                "Aposentou-se pela especial e continua ou voltou a trabalhar no mesmo ambiente.",
                "É constitucional vedar a aposentadoria especial a quem permanece ou retorna à atividade "
                "nociva. A DIB é a DER, mas, implantado o benefício, a continuidade faz cessar o pagamento, sem "
                "cancelar o benefício.",
                '"Tema 709" STF "aposentadoria especial" atividade nociva', stf(709),
                "Modulação: preservadas decisões transitadas e valores recebidos de boa-fé até 23/02/2021."),
         ], lacunas="N2 e N3: sem precedente verificado além do conflito registrado."),
    sub("incapacidade", "Benefícios por incapacidade e auxílio-acidente",
         [r"auxilio[- ]doenca", r"incapacidad", r"invalidez", r"afastad", r"afastamento", r"pericia",
          r"\balta\b", r"acidente", r"sequela", r"auxilio[- ]acidente", r"lesao", r"nao consig\w* trabalhar",
          r"encostad"],
         [
             p("STJ, Tema 1013", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Trabalhou enquanto esperava o benefício",
                "O INSS negou o auxílio e o cliente continuou trabalhando doente até a Justiça decidir.",
                "Entre o indeferimento e a implantação judicial do auxílio-doença ou da aposentadoria por "
                "invalidez, o segurado recebe juntos os salários do período e o benefício retroativo, ainda que "
                "o trabalho fosse incompatível com a incapacidade.",
                '"Tema 1013" STJ "recebimento conjunto" incapacidade', stj(1013)),
             p("STJ, Tema 862", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Início do auxílio-acidente",
                "Ficou com sequela; o auxílio-doença acabou e não recebeu mais nada.",
                "O auxílio-acidente começa no dia seguinte à cessação do auxílio-doença que lhe deu origem "
                "(Lei 8.213/1991, art. 86, § 2º), respeitada a prescrição de cinco anos (Súmula 85/STJ).",
                '"Tema 862" STJ "auxílio-acidente" "termo inicial"', stj(862)),
             p("STF, Tema 1125 (RE 1.298.832)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 20/09/2023",
                "Auxílio-doença conta como carência se intercalado",
                "Ficou um tempo afastado pelo INSS e depois voltou a trabalhar; quer saber se esse tempo conta.",
                "É constitucional contar, para carência, o período em auxílio-doença, desde que intercalado "
                "com períodos de atividade.",
                '"Tema 1125" STF carência "auxílio-doença" intercalado', stf(1125)),
             p("TNU, Súmula 47", "N2", "súmula da TNU, Juizados Especiais Federais", "VIGENTE",
                "enunciado conferido no CJF",
                "Incapacidade parcial e condições pessoais",
                "O perito disse que pode fazer serviço leve, mas o cliente tem idade, pouca instrução e só "
                "sabe trabalhar braçal.",
                "Reconhecida a incapacidade parcial, o juiz deve analisar as condições pessoais e sociais do "
                "segurado para a concessão de aposentadoria por invalidez.",
                '"Súmula 47" TNU incapacidade parcial condições pessoais', tnu_sumula(47)),
             p("TNU, Tema 277", "N2", "tese de uniformização, Juizados Especiais Federais", "VIGENTE",
                "trânsito em julgado em 25/04/2022",
                "Alta programada exige pedido de prorrogação",
                "O benefício acabou na data marcada pelo INSS e o cliente não pediu prorrogação.",
                "Para continuar o benefício com DCB estimada, o segurado precisa ter pedido prorrogação "
                "(Lei 8.213/1991, art. 60, § 9º), recurso ou reconsideração, quando previstos; sem isso, não "
                "há interesse de agir.",
                '"Tema 277" TNU "alta programada" prorrogação', tnu_tema(277)),
             p("TRU4, Súmula 7", "N3", "súmula regional, Juizados Federais da 4ª Região", "EM ATENÇÃO",
                "anterior ao Tema 1125/STF, que acrescentou a exigência de intercalação",
                "Benefício por incapacidade como carência (4ª Região)",
                "Recebeu benefício por incapacidade e quer contar o período como carência.",
                "Computa-se para carência o período em que o segurado recebeu benefício por incapacidade.",
                '"Súmula 7" TRU4 carência incapacidade', TRU4_SUMULAS,
                "Aplique com a ressalva do Tema 1125/STF (N1): só se intercalado com atividade."),
         ]),
    sub("bpc", "BPC/LOAS",
         [r"\bbpc\b", r"\bloas\b", r"beneficio assistencial", r"assistencial", r"deficien", r"idos[oa]",
          r"65 anos", r"cadunico", r"miserab", r"autis", r"\btea\b", r"baixa renda", r"renda per capita"],
         [
             p("STF, Tema 27 (RE 567.985)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 11/12/2013",
                "Renda de 1/4 do salário mínimo não é critério único",
                "O INSS negou porque a renda da casa passa um pouco de 1/4 do salário mínimo por pessoa.",
                "O critério de renda per capita inferior a 1/4 do salário mínimo (LOAS, art. 20, § 3º) não é "
                "o único meio de aferir a miserabilidade, que pode ser provada por outros elementos do caso.",
                '"Tema 27" STF "RE 567985" miserabilidade', stf(27),
                "A Lei 15.077/2024 alterou o art. 20 da LOAS (biometria, soma dos rendimentos do grupo "
                "familiar); confira o texto vigente."),
             p("STF, Tema 312 (RE 580.963)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 13/02/2014",
                "Benefício de um salário mínimo de outro membro fica fora da renda",
                "Alguém da casa recebe aposentadoria ou BPC de um salário mínimo e o INSS somou na renda.",
                "É inconstitucional, por omissão parcial, o art. 34, parágrafo único, do Estatuto do Idoso: "
                "benefício de um salário mínimo de idoso ou pessoa com deficiência do grupo familiar também "
                "deve ser excluído do cálculo da renda per capita.",
                '"Tema 312" STF "RE 580963" renda per capita', stf(312)),
             p("STJ, Tema 185", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Miserabilidade por outros meios de prova",
                "A renda declarada não reflete as despesas reais da família (remédios, aluguel, cuidados).",
                "Renda per capita inferior a 1/4 do salário mínimo gera presunção absoluta de miserabilidade; "
                "acima disso, ela pode ser demonstrada por outros meios de prova.",
                '"Tema 185" STJ "benefício assistencial" "outros meios"', stj(185)),
             p("TNU, Súmula 80", "N2", "súmula da TNU, Juizados Especiais Federais", "VIGENTE",
                "enunciado conferido no CJF",
                "Avaliação social no BPC da pessoa com deficiência",
                "O pedido de BPC por deficiência foi analisado só com perícia médica.",
                "Após a Lei 12.470/2011, o BPC da pessoa com deficiência exige avaliação social por assistente "
                "social, ou outra providência que revele as condições reais de vida do requerente.",
                '"Súmula 80" TNU "avaliação social" LOAS', tnu_sumula(80)),
         ], lacunas="N3: sem precedente verificado (a Súmula 6 da TRU4 sobre renda foi cancelada)."),
    sub("pensao", "Pensão por morte e dependentes",
         [r"pensao", r"obito", r"falece", r"falecid", r"\bmorte\b", r"viuv", r"companheir", r"uniao estavel",
          r"dependent", r"amante", r"concubin", r"segunda familia"],
         [
             p("STF, Tema 529 (RE 1.045.273)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 29/05/2021",
                "Uniões simultâneas não dividem a pensão",
                "O falecido era casado ou vivia com outra pessoa e mantinha também a relação com a cliente.",
                "Casamento ou união estável preexistente impede reconhecer outra união concomitante, inclusive "
                "para fins previdenciários, pelo dever de fidelidade e pela monogamia.",
                '"Tema 529" STF uniões concomitantes pensão', stf(529),
                "Separação de fato do primeiro vínculo muda a análise; confira os fatos."),
             p("STF, Tema 526 (RE 883.168)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 02/04/2022",
                "Concubinato com pessoa casada não gera pensão",
                "Manteve por anos relação com pessoa casada que não se separou.",
                "É incompatível com a Constituição reconhecer pensão por morte a quem manteve, por longo "
                "período e com aparência familiar, união com pessoa casada.",
                '"Tema 526" STF concubinato pensão', stf(526)),
             p("TNU, Súmula 63", "N2", "súmula da TNU, Juizados Especiais Federais", "ALTERADO",
                "enunciado alterado em 18/09/2025",
                "Prova da união estável depende da data do óbito",
                "Viveram juntos por anos, mas não há documento, só testemunhas.",
                "Para óbitos até a MP 871/2019, a união estável pode ser provada sem início de prova material. "
                "Para óbitos posteriores, vale a exigência legal de início de prova material contemporânea "
                "(Lei 8.213/1991, art. 16, § 5º; confira o texto).",
                '"Súmula 63" TNU "união estável" "MP 871"', tnu_sumula(63)),
             p("TRF4, Súmula 104", "N3", "súmula regional, TRF4", "EM ATENÇÃO",
                "editada em 2016, antes da MP 871/2019",
                "Prova testemunhal da união estável (4ª Região)",
                "Só há testemunhas da convivência, e o caso tramita no RS, SC ou PR.",
                "A legislação previdenciária não restringe a prova testemunhal para comprovar união estável.",
                '"Súmula 104" TRF4 "união estável" testemunhal', TRF4_SUMULAS,
                "Use só para óbitos anteriores à MP 871/2019 (veja a Súmula 63 da TNU alterada)."),
         ]),
    sub("rural", "Rural, segurado especial e aposentadoria híbrida",
         [r"\brural", r"\broca\b", r"lavoura", r"agricultor", r"boia[- ]fria", r"safrista", r"\bsitio\b",
          r"chacara", r"\bcolon[oa]", r"pescador", r"segurado especial", r"hibrida", r"produtor rural",
          r"bloco de produtor", r"\bitr\b"],
         [
             p("STJ, Tema 554", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Boia-fria e início de prova material",
                "Trabalhou na roça como diarista ou boia-fria, sem carteira, e tem poucos papéis.",
                "Aplica-se a Súmula 149/STJ ao boia-fria: só testemunhas não bastam, é preciso início de prova "
                "material. Prova material de só parte do período, ampliada por testemunhas robustas, basta.",
                '"Tema 554" STJ "boia-fria" "Súmula 149"', stj(554),
                "Tema 638/STJ (Súmula 577): dá para reconhecer tempo anterior ao documento mais antigo, com "
                "prova testemunhal convincente."),
             p("STJ, Tema 642", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado em 08/09/2016",
                "Segurado especial deve estar no campo ao completar a idade",
                "Trabalhou na roça a vida toda, mas há alguns anos mudou para a cidade.",
                "Para a aposentadoria por idade rural, o segurado especial deve estar no campo quando completa "
                "a idade, ressalvado o direito adquirido de quem já reunia antes idade e carência.",
                '"Tema 642" STJ segurado especial "período imediatamente anterior"', stj(642),
                "Se já não está no campo, avalie a aposentadoria híbrida (Tema 1007/STJ)."),
             p("STJ, Tema 1007", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Aposentadoria híbrida com tempo rural antigo",
                "Trabalhou na roça quando jovem, antes de 1991, e depois na cidade com carteira.",
                "Tempo rural, ainda que remoto e descontínuo, anterior à Lei 8.213/1991, conta para a carência "
                "da aposentadoria híbrida por idade, sem recolhimentos, qualquer que seja o trabalho "
                "predominante ou o exercido ao completar a idade.",
                '"Tema 1007" STJ "aposentadoria híbrida" "rural remoto"', stj(1007)),
             p("TNU, Súmula 14", "N2", "súmula da TNU, Juizados Especiais Federais", "VIGENTE",
                "enunciado conferido no CJF",
                "Prova material não precisa cobrir toda a carência",
                "Tem documentos rurais de alguns anos, não de todo o período.",
                "Na aposentadoria rural por idade, o início de prova material não precisa corresponder a todo "
                "o período de carência.",
                '"Súmula 14" TNU "início de prova material" carência', tnu_sumula(14)),
             p("TNU, Súmula 34", "N2", "súmula da TNU, Juizados Especiais Federais", "VIGENTE",
                "enunciado conferido no CJF",
                "Prova material contemporânea",
                "Os documentos rurais foram feitos recentemente, sobre fatos antigos.",
                "Para comprovar labor rural, o início de prova material deve ser contemporâneo à época dos fatos.",
                '"Súmula 34" TNU contemporâneo rural', tnu_sumula(34)),
             p("TRU4, Súmula 9", "N3", "súmula regional, Juizados Federais da 4ª Região", "VIGENTE",
                "enunciado conferido no portal do TRF4",
                "Documentos em nome da família (4ª Região)",
                "Os documentos da roça estão no nome do pai, do marido ou de outro membro da família.",
                "Admitem-se como início de prova material documentos em nome de integrantes do grupo familiar "
                "em regime de economia familiar rural.",
                '"Súmula 9" TRU4 "economia familiar"', TRU4_SUMULAS,
                "A Súmula 14 da TRU4 (boia-fria sem prova material) conflita com o Tema 554/STJ, que prevalece."),
         ]),
    sub("revisoes", "Revisões, decadência e cálculo",
         [r"revis", r"recalcul", r"vida toda", r"decadenc", r"\brmi\b", r"valor da aposentadoria",
          r"aumentar a aposentadoria", r"calcul\w* errad"],
         [
             p("STF, Tema 1102 (RE 1.276.977)", "N1", "tese de repercussão geral, nacional", "SUPERADO",
                "tese favorável cancelada após as ADIs 2.110 e 2.111; trânsito em julgado em 15/05/2026",
                "Revisão da vida toda não existe mais",
                "Ouviu falar da revisão da vida toda e quer pedir.",
                "As ADIs 2.110 e 2.111 validaram a regra de transição da Lei 9.876/1999 como obrigatória, e a "
                "tese de 2022 foi cancelada. O segurado não pode optar pela regra definitiva mais favorável.",
                '"Tema 1102" STF "vida toda" "ADI 2110"', stf(1102),
                "Não use como fundamento. Fontes secundárias dizem que não há devolução do que foi recebido "
                "por decisões até 05/04/2024; confira no acórdão."),
             p("STF, Tema 313 (RE 626.489)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 08/10/2014",
                "Decadência de 10 anos para revisar",
                "Aposentou-se há mais de 10 anos e acha que o cálculo saiu errado.",
                "Não há prazo decadencial para pedir a concessão inicial do benefício; para revisar benefício "
                "já concedido vale o prazo de 10 anos, inclusive para os concedidos antes da MP 1.523/1997.",
                '"Tema 313" STF decadência revisão "RE 626489"', stf(313)),
             p("STJ, Tema 975", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Decadência alcança o que o INSS não analisou",
                "Quer incluir na revisão um período que o INSS nem examinou na concessão.",
                "O prazo de 10 anos (Lei 8.213/1991, art. 103) vale também quando a questão não foi apreciada "
                "pelo INSS no ato de concessão.",
                '"Tema 975" STJ decadência "não apreciada"', stj(975)),
         ], lacunas="N2 e N3: sem precedente verificado."),
]
