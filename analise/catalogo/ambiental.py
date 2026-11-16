"""Direito Ambiental: precedentes curados (conferidos em 16/11/2026: STF — página do tema e tese oficial —, STJ —
temas e PDF oficial de súmulas)."""
from .base import p, stf, stj, stj_sumula, sub

ALCANCE = "regional do TRF4 ou do TJ indicado (RS, SC ou PR), só para casos que tramitam lá"

SUBAREAS = [
    sub("dano-ambiental", "Dano ambiental: responsabilidade, reparação e prova",
        [r"dano ambiental", r"poluic", r"contamina", r"vazamento", r"desmatament", r"degradac", r"rio\b",
         r"pescador", r"\bpesca\b", r"rompimento", r"barragem", r"queimada", r"lixo", r"meio ambiente"],
        [
            p("STJ, Tema 681", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Responsabilidade ambiental objetiva pelo risco integral",
              "Uma empresa poluiu o rio e o pescador ou morador perdeu renda ou saúde.",
              "A responsabilidade por dano ambiental é objetiva, pela teoria do risco integral; a empresa não pode "
              "invocar excludentes (caso fortuito, força maior, fato de terceiro) para se eximir.",
              '"Tema 681" STJ dano ambiental risco integral excludentes', stj(681),
              "O mesmo julgamento (Tema 707/STJ) admite danos materiais e morais aos atingidos."),
            p("STF, Tema 999 (RE 654.833)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 19/08/2020",
              "Reparação de dano ambiental não prescreve",
              "O dano ambiental aconteceu há muitos anos e o causador alega prescrição.",
              "É imprescritível a pretensão de reparação civil de dano ambiental.",
              '"Tema 999" STF imprescritibilidade dano ambiental', stf(999),
              "Cuidado: a indenização individual por dano pessoal ou patrimonial do atingido pode ter prazo próprio."),
            p("STJ, Súmula 618", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Inversão do ônus da prova na degradação ambiental",
              "O cliente atingido não tem como provar tecnicamente a origem da poluição.",
              "A inversão do ônus da prova aplica-se às ações de degradação ambiental.",
              '"Súmula 618" STJ inversão ônus degradação ambiental', stj_sumula(618),
              "Admite-se cumular obrigação de fazer ou não fazer com indenização (Súmula 629/STJ)."),
            p("STJ, Súmula 623", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Obrigação ambiental acompanha o imóvel",
              "O cliente comprou uma área já degradada e agora cobram dele a recuperação.",
              "As obrigações ambientais são propter rem: podem ser cobradas do proprietário ou possuidor atual e/ou "
              "dos anteriores, à escolha do credor.",
              '"Súmula 623" STJ propter rem obrigação ambiental', stj_sumula(623),
              "Desfavorável ao adquirente: avalie regresso contra o vendedor."),
        ], lacunas="N3: sem precedente verificado."),
    sub("app-ocupacao", "Áreas de preservação, construção e ocupação",
        [r"\bapp\b", r"preservacao permanente", r"margem", r"curso d.agua", r"arroio", r"nascente", r"mata ciliar",
         r"codigo florestal", r"reserva legal", r"embargo", r"demolic", r"construcao irregular"],
        [
            p("STJ, Tema 1010", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "APP de curso d'água em área urbana segue o Código Florestal",
              "O cliente construiu perto de um rio ou arroio dentro da cidade.",
              "Na vigência do Código Florestal (Lei 12.651/2012), a faixa não edificável das APPs de cursos d'água, "
              "inclusive em área urbana consolidada, segue o art. 4º, I, do Código.",
              '"Tema 1010" STJ APP curso d\'água área urbana consolidada', stj(1010),
              "Desfavorável a quem construiu: verifique leis posteriores sobre faixas em área urbana consolidada."),
            p("STJ, Súmula 613", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Sem fato consumado no direito ambiental",
              "A construção está ali há muitos anos e o cliente diz que a situação já se consolidou.",
              "Não se admite a teoria do fato consumado em direito ambiental.",
              '"Súmula 613" STJ fato consumado ambiental', stj_sumula(613)),
        ], lacunas="N3: sem precedente verificado."),
    sub("multas-ambientais", "Multas e infrações ambientais",
        [r"multa ambiental", r"auto de infracao", r"\bibama\b", r"fepam", r"\bima\b", r"\biat\b",
         r"infracao ambiental", r"fiscalizacao ambiental", r"prescricao da multa"],
        [
            p("STJ, Tema 328", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Processo administrativo parado três anos prescreve",
              "O processo do auto de infração ficou parado por anos no órgão ambiental.",
              "É de três anos o prazo para concluir o processo administrativo de apuração da infração (prescrição "
              "intercorrente).",
              '"Tema 328" STJ prescrição intercorrente processo administrativo infração', stj(328)),
            p("STJ, Tema 324", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Cinco anos para constituir a multa",
              "A infração é antiga e só agora o órgão lavrou o auto.",
              "É de cinco anos o prazo decadencial para constituir o crédito de infração à legislação administrativa "
              "(conta-se da infração; na infração continuada, do dia em que cessou — Temas 325 e 326/STJ).",
              '"Tema 324" STJ decadência infração administrativa cinco anos', stj(324)),
            p("STJ, Súmula 467", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Cobrança da multa ambiental: cinco anos após o processo",
              "A multa foi confirmada há anos e só agora o órgão cobra.",
              "Prescreve em cinco anos, contados do fim do processo administrativo, a execução da multa por infração "
              "ambiental.",
              '"Súmula 467" STJ multa ambiental prescrição', stj_sumula(467)),
        ], lacunas="N3: sem precedente verificado."),
]
