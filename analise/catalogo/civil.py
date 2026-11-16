"""Direito Civil: precedentes curados (conferidos em 16/11/2026 no STJ — temas e PDF oficial de súmulas — e
na lista oficial de IRDRs do TJPR)."""
from .base import p, stj, stj_sumula, sub

TJPR_IRDR = "https://ejud.tjpr.jus.br/web/guest/nugep-irdr-admitidos"

ALCANCE = "regional do TJ indicado (RS, SC ou PR), só para casos que tramitam lá"

SUBAREAS = [
    sub("responsabilidade-civil", "Responsabilidade civil e indenização",
        [r"indeniza", r"dano moral", r"dano material", r"dano estetic", r"lucros? cessantes", r"acidente",
         r"colisao", r"batida", r"atropel", r"responsabilidade civil", r"prejuizo", r"difama", r"calunia",
         r"ofens"],
        [
            p("STJ, Tema 1368", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Juros de mora nas dívidas civis: SELIC",
              "O cliente cobra uma indenização ou dívida antiga e quer saber como corrigir o valor.",
              "Antes da Lei 14.905/2024, o art. 406 do Código Civil manda aplicar a SELIC como taxa de juros de "
              "mora nas dívidas civis.",
              '"Tema 1368" STJ SELIC "art. 406"', stj(1368),
              "A partir da Lei 14.905/2024, valem a correção pelo IPCA e os juros pela taxa legal do novo art. 406 "
              "(confira o texto e a data de vigência)."),
            p("STJ, Súmula 54", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Juros desde o evento danoso no ilícito extracontratual",
              "O dano veio de um acidente ou ofensa, sem contrato entre as partes.",
              "Os juros moratórios fluem a partir do evento danoso, em caso de responsabilidade extracontratual.",
              '"Súmula 54" STJ "evento danoso"', stj_sumula(54),
              "A correção do dano moral corre desde o arbitramento (Súmula 362/STJ)."),
            p("STJ, Súmula 387", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Dano estético e dano moral se somam",
              "O acidente deixou cicatriz, deformidade ou sequela visível, além do sofrimento.",
              "É lícita a cumulação das indenizações de dano estético e dano moral.",
              '"Súmula 387" STJ "dano estético"', stj_sumula(387),
              "Material e moral também são cumuláveis (Súmula 37/STJ); pessoa jurídica pode sofrer dano moral "
              "(Súmula 227/STJ)."),
        ], lacunas="N3: sem precedente verificado."),
    sub("cobranca-titulos", "Cobrança, monitória e títulos de crédito",
        [r"cobranc", r"divida", r"nao (me )?pag", r"calote", r"nota promissoria", r"cheque", r"monitori",
         r"confissao de divida", r"inadimpl", r"emprestei"],
        [
            p("STJ, Tema 564", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Monitória de cheque prescrito sem explicar o negócio",
              "Tem um cheque antigo, já sem força de execução, e quer cobrar.",
              "Na ação monitória fundada em cheque prescrito, ajuizada contra o emitente, é dispensável mencionar o "
              "negócio jurídico que originou o cheque.",
              '"Tema 564" STJ monitória "cheque prescrito"', stj(564),
              "Mesmo entendimento na Súmula 531/STJ."),
            p("STJ, Súmula 503", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Prazo da monitória de cheque: cinco anos",
              "O cheque não foi compensado há alguns anos.",
              "O prazo para a monitória contra o emitente de cheque sem força executiva é de cinco anos, a contar do "
              "dia seguinte à data de emissão do cheque.",
              '"Súmula 503" STJ monitória cheque prazo', stj_sumula(503),
              "Para nota promissória sem força executiva, cinco anos do dia seguinte ao vencimento (Súmula 504/STJ)."),
            p("STJ, Súmula 247", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Monitória com contrato de crédito em conta e extrato",
              "O banco ou credor tem o contrato de limite em conta e o demonstrativo do débito.",
              "O contrato de abertura de crédito em conta-corrente, acompanhado do demonstrativo de débito, é "
              "documento hábil para a ação monitória.",
              '"Súmula 247" STJ monitória "abertura de crédito"', stj_sumula(247)),
        ], lacunas="N3: sem precedente verificado."),
    sub("execucao-penhora", "Execução, penhora e bem de família",
        [r"penhor", r"bloquei", r"sisbajud", r"bacenjud", r"conta bloqueada", r"salario bloqueado", r"poupanca",
         r"execucao", r"cumprimento de sentenca", r"bem de familia", r"imovel penhorado", r"fiador", r"leilao"],
        [
            p("STJ, Tema 1230", "N1", "tese repetitiva, nacional", "EM ATENÇÃO",
              "acórdão publicado, sem trânsito em julgado", "Penhora parcial de salário para dívida comum",
              "O credor pediu bloqueio de parte do salário do devedor numa dívida que não é de pensão.",
              "A impenhorabilidade do salário (CPC, art. 833, IV) pode ser mitigada, excepcionalmente, em dívida não "
              "alimentar, se esgotados os outros meios de execução e se a penhora não comprometer a subsistência "
              "digna do devedor e da família; o ônus dessa prova é do devedor.",
              '"Tema 1230" STJ penhora salário "subsistência digna"', stj(1230)),
            p("STJ, Tema 1285", "N1", "tese repetitiva, nacional", "EM ATENÇÃO",
              "acórdão publicado, sem trânsito em julgado", "Até 40 salários mínimos de reserva são impenhoráveis",
              "Bloquearam dinheiro da poupança, da conta ou de uma aplicação do cliente.",
              "É impenhorável até 40 salários mínimos em poupança, papel-moeda, conta corrente ou investimento com "
              "caráter de reserva duradoura para emergências; não se aplica a aplicações especulativas de alto risco "
              "nem às sobras de meses anteriores em conta corrente.",
              '"Tema 1285" STJ "40 salários-mínimos" impenhorável', stj(1285),
              "Não é matéria de ordem pública: alegue na primeira oportunidade, sob pena de preclusão "
              "(Tema 1235/STJ)."),
            p("STJ, Tema 1091", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Bem de família do fiador de locação pode ser penhorado",
              "O cliente foi fiador de aluguel e querem penhorar a casa onde mora.",
              "É válida a penhora do bem de família do fiador de contrato de locação, residencial ou comercial "
              "(Lei 8.009/1990, art. 3º, VII).",
              '"Tema 1091" STJ fiador "bem de família"', stj(1091)),
            p("STJ, Súmula 375", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Fraude à execução exige registro ou má-fé",
              "O cliente comprou um bem que depois disseram estar em fraude à execução.",
              "O reconhecimento da fraude à execução depende do registro da penhora do bem alienado ou da prova de "
              "má-fé do terceiro adquirente.",
              '"Súmula 375" STJ "fraude à execução"', stj_sumula(375)),
            p("STJ, Súmula 364", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Bem de família de quem mora sozinho",
              "O devedor é solteiro, separado ou viúvo e mora sozinho no imóvel.",
              "A impenhorabilidade do bem de família abrange também o imóvel de pessoas solteiras, separadas e viúvas.",
              '"Súmula 364" STJ "bem de família" solteiras', stj_sumula(364)),
            p("TJPR, IRDR 40", "N3", "IRDR, só no Paraná", "VIGENTE", "transitado em julgado",
              "Pequena propriedade rural: o devedor prova a impenhorabilidade (PR)",
              "Querem penhorar o sítio do cliente no Paraná, que ele diz ser pequena propriedade rural.",
              "É ônus do executado provar que o imóvel é pequena propriedade rural e que se destina à exploração "
              "para renda e subsistência da família ou à moradia permanente (Constituição, art. 5º, XXVI; CPC, art. "
              "833, VIII).",
              '"IRDR 40" TJPR "pequena propriedade rural" impenhorabilidade', TJPR_IRDR),
        ]),
    sub("custos-processo", "Gratuidade, honorários e custos do processo",
        [r"gratuidade", r"justica gratuita", r"assistencia judiciaria", r"\bcustas\b", r"honorario",
         r"sucumbenc", r"nao (tenho|tem) (como|dinheiro)"],
        [
            p("STJ, Tema 1178", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Gratuidade não pode ser negada por critério objetivo",
              "O juiz negou a justiça gratuita só porque o cliente ganha acima de um certo valor.",
              "É vedado indeferir de imediato a gratuidade da pessoa natural por critérios objetivos. Havendo "
              "elementos contra a presunção de hipossuficiência, o juiz deve intimar o requerente a comprová-la, "
              "dizendo as razões; critérios objetivos só podem ser suplementares.",
              '"Tema 1178" STJ gratuidade "critérios objetivos"', stj(1178)),
            p("STJ, Tema 1424", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Gratuidade da pessoa jurídica exige prova contábil",
              "A empresa do cliente está parada ou faturando pouco e quer justiça gratuita.",
              "A pessoa jurídica deve demonstrar a hipossuficiência com dados de ativo, passivo, patrimônio líquido, "
              "resultado, fluxo de caixa, participações e saldos bancários; prova de inatividade ou queda de "
              "faturamento não basta.",
              '"Tema 1424" STJ gratuidade "pessoa jurídica"', stj(1424),
              "Súmula 481/STJ: a pessoa jurídica com ou sem fins lucrativos tem direito se demonstrar a "
              "impossibilidade de pagar."),
            p("STJ, Tema 1076", "N1", "tese repetitiva, nacional", "EM ATENÇÃO",
              "acórdão publicado; recurso extraordinário pendente",
              "Honorários por equidade só em causa de valor baixo ou inestimável",
              "A causa vale muito e o juiz fixou honorários num valor fixo pequeno.",
              "Com condenação, causa ou proveito econômico elevados, os honorários seguem os percentuais do art. 85, "
              "§§ 2º e 3º, do CPC; a equidade só cabe se o proveito for inestimável ou irrisório, ou o valor da causa "
              "muito baixo.",
              '"Tema 1076" STJ honorários equidade', stj(1076)),
        ], lacunas="N2 e N3: sem precedente verificado além do citado no alerta."),
    sub("seguros", "Seguros de vida e de danos",
        [r"seguro", r"segurador", r"apolice", r"sinistro", r"segurad", r"\bpremio\b", r"suicid", r"embriag"],
        [
            p("STJ, Tema 1211", "N1", "tese repetitiva, nacional", "EM ATENÇÃO",
              "acórdão publicado, sem trânsito em julgado", "Reajuste do seguro de vida em grupo por idade",
              "O prêmio do seguro de vida em grupo subiu muito quando o cliente mudou de faixa etária.",
              "No seguro de vida em grupo, o reajuste por faixa etária é válido se previsto expressamente, com aviso "
              "prévio nas renovações e respeito às normas da SUSEP e do CNSP; não se aplicam por analogia a Lei dos "
              "Planos de Saúde e o Estatuto do Idoso.",
              '"Tema 1211" STJ "seguro de vida em grupo" "faixa etária"', stj(1211)),
            p("STJ, Tema 1112", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Quem informa as cláusulas no seguro coletivo",
              "A seguradora negou com base numa cláusula restritiva que o cliente diz nunca ter conhecido.",
              "No seguro de vida coletivo com estipulação própria, o dever de informar previamente os segurados "
              "sobre as condições, inclusive cláusulas limitativas, é exclusivamente do estipulante. Estipulação "
              "imprópria ou falso estipulante: a apólice é tratada como individual.",
              '"Tema 1112" STJ estipulante "dever de informação"', stj(1112)),
            p("STJ, Tema 1068", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Cobertura por invalidez funcional (IFPD)",
              "O seguro negou a invalidez por doença porque o cliente ainda consegue cuidar de si.",
              "Não é abusiva a cláusula da cobertura de invalidez funcional permanente total por doença (IFPD) que "
              "condiciona a indenização à perda da existência independente do segurado, comprovada por declaração "
              "médica.",
              '"Tema 1068" STJ IFPD invalidez funcional', stj(1068),
              "Desfavorável ao segurado: verifique se o contrato é IFPD ou outra cobertura antes de ajuizar."),
            p("STJ, Súmula 616", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Atraso no prêmio sem aviso não tira a cobertura",
              "O cliente atrasou uma parcela do seguro e, depois do sinistro, a seguradora negou.",
              "A indenização é devida se não houve comunicação prévia ao segurado sobre o atraso do prêmio, requisito "
              "para suspender ou resolver o contrato.",
              '"Súmula 616" STJ atraso prêmio comunicação', stj_sumula(616)),
            p("STJ, Súmula 620", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Embriaguez não afasta o seguro de vida",
              "O segurado morreu num acidente e havia bebido; a seguradora recusou.",
              "A embriaguez do segurado não exime a seguradora de pagar a indenização do seguro de vida.",
              '"Súmula 620" STJ embriaguez "seguro de vida"', stj_sumula(620),
              "Suicídio nos dois primeiros anos não é coberto, com devolução da reserva técnica (Súmula 610/STJ)."),
        ], lacunas="N3: sem precedente verificado."),
]
