"""Direito Tributário: precedentes curados (conferidos em 16/11/2026: STF — página do tema e tese oficial —, STJ —
temas e PDF oficial de súmulas —, lista oficial de IRDRs do TJPR)."""
from .base import p, stf, stj, stj_sumula, sub

TJPR_IRDR = "https://ejud.tjpr.jus.br/web/guest/nugep-irdr-admitidos"

ALCANCE = "regional do TRF4 ou do TJ indicado (RS, SC ou PR), só para casos que tramitam lá"

SUBAREAS = [
    sub("execucao-fiscal", "Execução fiscal, prescrição e redirecionamento ao sócio",
        [r"execucao fiscal", r"divida ativa", r"\bcda\b", r"receita federal", r"fazenda", r"procuradoria",
         r"prescricao intercorrente", r"redireciona", r"\bsocio\b", r"empresa fechou", r"protesto", r"pgfn"],
        [
            p("STJ, Tema 566", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Prescrição intercorrente começa sozinha",
              "A execução fiscal ficou parada anos sem achar bens do devedor.",
              "O ano de suspensão do art. 40 da Lei 6.830/1980 começa automaticamente quando a Fazenda toma ciência "
              "de que o devedor ou seus bens não foram localizados; findo o ano, começa o prazo prescricional.",
              '"Tema 566" STJ prescrição intercorrente "art. 40" LEF', stj(566),
              "Só a efetiva penhora ou citação interrompem a intercorrente, não meros pedidos (Tema 568/STJ). "
              "Súmula 314/STJ no mesmo sentido."),
            p("STJ, Tema 981", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Redirecionamento: responde quem administrava na dissolução",
              "A empresa fechou sem baixa e a Fazenda quer cobrar do sócio.",
              "Na dissolução irregular, o redirecionamento atinge o sócio ou terceiro com poderes de administração "
              "na data da dissolução, mesmo que não gerisse a empresa quando o tributo venceu (CTN, art. 135, III).",
              '"Tema 981" STJ redirecionamento dissolução irregular', stj(981),
              "Quem saiu antes da dissolução não responde por ela (Tema 962/STJ)."),
            p("STF, Tema 1184 (RE 1.355.208)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 14/10/2025",
              "Execução fiscal de baixo valor pode ser extinta",
              "A cobrança judicial é de valor pequeno e não houve tentativa de acordo nem protesto.",
              "É legítimo extinguir execução fiscal de baixo valor por falta de interesse de agir. O ajuizamento "
              "depende de tentativa prévia de conciliação ou solução administrativa e de protesto do título, salvo "
              "justificativa de eficiência.",
              '"Tema 1184" STF execução fiscal baixo valor protesto', stf(1184)),
            p("STJ, Súmula 435", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Presunção de dissolução irregular",
              "A empresa não funciona mais no endereço fiscal e não avisou a Receita.",
              "Presume-se dissolvida irregularmente a empresa que deixa de funcionar no domicílio fiscal sem "
              "comunicar os órgãos competentes, o que permite redirecionar ao sócio-gerente.",
              '"Súmula 435" STJ dissolução irregular domicílio fiscal', stj_sumula(435)),
            p("STJ, Súmula 393", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Exceção de pré-executividade",
              "O cliente quer se defender sem garantir o juízo, alegando prescrição ou ilegitimidade.",
              "A exceção de pré-executividade é admissível na execução fiscal para matérias conhecíveis de ofício que "
              "não exijam produção de provas.",
              '"Súmula 393" STJ exceção de pré-executividade', stj_sumula(393)),
            p("TJPR, IRDR 9", "N3", "IRDR, só no Paraná", "VIGENTE", "transitado em julgado",
              "Devedor morreu antes da execução: redireciona ao espólio (PR)",
              "O contribuinte morreu depois do lançamento e antes da execução, no Paraná.",
              "Pode-se alterar o polo passivo da execução fiscal, redirecionando ao espólio, se a morte ocorreu após o "
              "lançamento e antes da propositura.",
              '"IRDR 9" TJPR execução fiscal espólio', TJPR_IRDR),
        ]),
    sub("ir-pessoa-fisica", "Imposto de renda da pessoa física: isenções e não incidência",
        [r"imposto de renda", r"\birpf?\b", r"isencao", r"molestia grave", r"doenca grave", r"cancer",
         r"neoplasia", r"aposentad", r"juros de mora", r"leao"],
        [
            p("STJ, Tema 250", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Isenção por moléstia grave: rol fechado",
              "O cliente aposentado tem uma doença e quer isenção do IR.",
              "A isenção do art. 6º, XIV, da Lei 7.713/1988 vale para os aposentados com as moléstias listadas na lei "
              "(câncer, cardiopatia grave, Parkinson, entre outras), mesmo contraídas após a aposentadoria; o rol é "
              "taxativo.",
              '"Tema 250" STJ isenção moléstia grave rol taxativo', stj(250),
              "Não se exige sintomas atuais nem recidiva (Súmula 627/STJ)."),
            p("STJ, Tema 1037", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Quem ainda trabalha não tem a isenção",
              "O cliente tem doença grave, mas continua trabalhando e recebendo salário.",
              "A isenção do art. 6º, XIV, da Lei 7.713/1988 não se aplica aos rendimentos de portador de moléstia "
              "grave em atividade laboral.",
              '"Tema 1037" STJ isenção moléstia grave atividade', stj(1037),
              "Desfavorável: a isenção alcança proventos de aposentadoria, reforma e pensão."),
            p("STF, Tema 808 (RE 855.091)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 09/10/2021",
              "Sem IR sobre juros de mora de verbas do trabalho",
              "O cliente recebeu atrasados de salário com juros e houve retenção de IR sobre os juros.",
              "Não incide imposto de renda sobre juros de mora pelo atraso no pagamento de remuneração por emprego, "
              "cargo ou função.",
              '"Tema 808" STF imposto de renda juros de mora', stf(808)),
            p("STJ, Súmula 598", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Laudo oficial não é obrigatório em juízo",
              "O cliente tem laudos particulares, mas não o laudo do serviço médico oficial.",
              "É desnecessário laudo médico oficial para o reconhecimento judicial da isenção do IR se a doença grave "
              "estiver demonstrada por outros meios.",
              '"Súmula 598" STJ laudo oficial isenção', stj_sumula(598)),
            p("STJ, Súmula 627", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Isenção sem sintomas atuais",
              "O câncer do cliente está controlado e a Receita quer cortar a isenção.",
              "O contribuinte tem direito à concessão ou manutenção da isenção do IR sem demonstrar sintomas "
              "contemporâneos nem recidiva.",
              '"Súmula 627" STJ isenção contemporaneidade sintomas', stj_sumula(627)),
        ], lacunas="N3: sem precedente verificado."),
    sub("icms-pis-cofins", "ICMS, PIS e COFINS: empresa e conta de luz",
        [r"\bicms\b", r"\bpis\b", r"cofins", r"conta de luz", r"energia eletrica", r"telecomunica", r"\btusd\b",
         r"\btust\b", r"aliquota", r"empresa paga", r"credito tributario"],
        [
            p("STF, Tema 69 (RE 574.706)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 09/09/2021",
              "ICMS fora da base do PIS e da COFINS",
              "A empresa do cliente recolheu PIS e COFINS com o ICMS na base.",
              "O ICMS não compõe a base de cálculo do PIS e da COFINS.",
              '"Tema 69" STF ICMS base PIS COFINS', stf(69),
              "Há modulação (efeitos a partir de 15/03/2017, ressalvadas ações anteriores); confira antes de pedir "
              "restituição."),
            p("STF, Tema 745 (RE 714.139)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 30/06/2022",
              "ICMS de energia e telecom não pode ser maior que o geral",
              "A alíquota de ICMS na conta de luz ou telefone é maior que a das mercadorias em geral.",
              "Adotada a seletividade, são inconstitucionais alíquotas de ICMS sobre energia elétrica e "
              "telecomunicações acima das operações em geral, pela essencialidade.",
              '"Tema 745" STF seletividade ICMS energia telecomunicações', stf(745),
              "Há modulação; confira o marco temporal antes de pedir restituição."),
            p("STJ, Tema 986", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "TUSD e TUST entram na base do ICMS",
              "O cliente quer tirar a TUSD/TUST do ICMS da conta de luz.",
              "TUST e TUSD lançadas na fatura como encargo do consumidor final (livre ou cativo) integram a base do "
              "ICMS (LC 87/1996, art. 13, § 1º, II, a).",
              '"Tema 986" STJ TUSD TUST base ICMS', stj(986),
              "Desfavorável ao contribuinte: não ajuíze essa tese sem fato novo."),
        ], lacunas="N2 e N3: sem precedente verificado."),
    sub("impostos-imovel", "IPTU, ITBI e impostos sobre imóveis",
        [r"\biptu\b", r"\bitbi\b", r"\bitcmd\b", r"escritura", r"compra de imovel", r"transmissao",
         r"valor venal", r"prefeitura cobra", r"carne"],
        [
            p("STJ, Tema 1113", "N1", "tese repetitiva, nacional", "EM ATENÇÃO",
              "acórdão publicado; recurso extraordinário pendente",
              "ITBI sobre o valor declarado, não sobre tabela da prefeitura",
              "A prefeitura cobrou ITBI sobre um valor de referência maior que o preço pago.",
              "A base do ITBI é o valor de mercado do imóvel, sem vínculo com o IPTU. O valor declarado presume-se de "
              "mercado e só pode ser afastado por processo administrativo (CTN, art. 148); o Município não pode "
              "arbitrar a base por valor de referência unilateral.",
              '"Tema 1113" STJ ITBI base de cálculo valor declarado', stj(1113)),
            p("STJ, Tema 980", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Prescrição do IPTU conta do vencimento",
              "A prefeitura cobra IPTU de muitos anos atrás.",
              "A prescrição da cobrança do IPTU começa no dia seguinte ao vencimento; parcelamento de ofício não "
              "interrompe a prescrição, porque o contribuinte não anuiu.",
              '"Tema 980" STJ prescrição IPTU vencimento parcelamento de ofício', stj(980)),
            p("STJ, Tema 122", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Quem paga o IPTU: comprador ou dono registrado",
              "O imóvel foi vendido por contrato, mas segue no nome do vendedor, e o IPTU veio para ele.",
              "Tanto o promitente comprador (possuidor) quanto o proprietário registrado são contribuintes do IPTU; "
              "cabe à lei municipal definir o sujeito passivo.",
              '"Tema 122" STJ IPTU promitente comprador proprietário', stj(122),
              "Mesmo sentido na Súmula 399/STJ."),
            p("STJ, Súmula 397", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Carnê do IPTU vale como notificação",
              "O cliente diz que nunca foi notificado do IPTU cobrado.",
              "O contribuinte do IPTU é notificado do lançamento pelo envio do carnê ao seu endereço.",
              '"Súmula 397" STJ IPTU carnê notificação', stj_sumula(397),
              "Desfavorável: a defesa precisa provar que não recebeu o carnê."),
        ], lacunas="N3: sem precedente verificado. ITBI só com o registro (Tema 1124/STF): situação não conferida."),
]
