"""Direito Administrativo: precedentes curados (conferidos em 16/11/2026: STF — página do tema e tese oficial —,
STJ — temas e PDF oficial de súmulas)."""
from .base import p, stf, stj, stj_sumula, sub

ALCANCE = "regional do TRF4 ou do TJ indicado (RS, SC ou PR), só para casos que tramitam lá"

SUBAREAS = [
    sub("concurso-publico", "Concurso público e nomeação",
        [r"concurso", r"aprovad", r"nomea", r"edital", r"cadastro de reserva", r"vagas", r"candidat",
         r"preteri", r"posse", r"\bpcd\b", r"visao monocular"],
        [
            p("STF, Tema 161 (RE 598.099)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 01/03/2013",
              "Aprovado dentro das vagas tem direito à nomeação",
              "O cliente passou dentro do número de vagas do edital e não foi chamado.",
              "O candidato aprovado dentro do número de vagas previsto no edital tem direito subjetivo à nomeação.",
              '"Tema 161" STF nomeação dentro das vagas', stf(161)),
            p("STF, Tema 784 (RE 837.311)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 04/05/2016",
              "Fora das vagas: só com preterição arbitrária",
              "O cliente ficou no cadastro de reserva e surgiram vagas ou abriram novo concurso.",
              "Novas vagas ou novo concurso durante a validade não geram, por si, direito à nomeação de quem ficou "
              "fora das vagas, salvo preterição arbitrária e imotivada que revele a necessidade inequívoca de "
              "nomear, provada pelo candidato.",
              '"Tema 784" STF preterição cadastro de reserva', stf(784),
              "Reúna prova da necessidade: terceirizados ou temporários na mesma função, vagas declaradas."),
            p("STJ, Tema 1094", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Diploma superior supre exigência de curso técnico",
              "O edital pedia ensino técnico e o cliente tem faculdade na mesma área.",
              "O aprovado pode assumir cargo que exige ensino médio técnico na área se tiver diploma de nível "
              "superior na mesma área profissional.",
              '"Tema 1094" STJ concurso técnico diploma superior', stj(1094)),
            p("STJ, Súmula 266", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Diploma se exige na posse",
              "O cliente se inscreveu antes de concluir o curso exigido.",
              "O diploma ou habilitação legal deve ser exigido na posse, não na inscrição no concurso.",
              '"Súmula 266" STJ diploma posse inscrição', stj_sumula(266)),
            p("STJ, Súmula 377", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Visão monocular concorre às vagas de deficiência",
              "O cliente enxerga só de um olho e foi excluído das vagas reservadas.",
              "O portador de visão monocular tem direito de concorrer às vagas reservadas a pessoas com deficiência.",
              '"Súmula 377" STJ visão monocular concurso', stj_sumula(377)),
        ], lacunas="N3: sem precedente verificado."),
    sub("servidor-remuneracao", "Servidor público: vantagens, progressão e prescrição",
        [r"servidor", r"progressao", r"promocao", r"adicional", r"gratifica", r"vencimento", r"abono de permanencia",
         r"reajuste", r"prefeitura nao paga", r"estatut"],
        [
            p("STJ, Tema 1075", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Limite da LRF não barra progressão devida",
              "O ente negou a progressão do servidor alegando limite de gastos com pessoal.",
              "É ilegal negar progressão funcional a servidor que cumpre os requisitos legais sob o argumento de "
              "que foram superados os limites de gasto com pessoal da Lei de Responsabilidade Fiscal.",
              '"Tema 1075" STJ progressão funcional LRF', stj(1075)),
            p("STJ, Tema 1233", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Abono de permanência entra no 13º e nas férias",
              "O servidor recebe abono de permanência e ele não entra no cálculo do 13º e do terço.",
              "O abono de permanência, de natureza remuneratória e permanente, integra a base das verbas calculadas "
              "sobre a remuneração, como adicional de férias e 13º salário.",
              '"Tema 1233" STJ abono de permanência férias 13º', stj(1233)),
            p("STJ, Tema 1410", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Prescrição do fundo de direito exige negativa expressa",
              "O ente nunca implantou uma vantagem prevista em lei e alega que tudo prescreveu.",
              "Nas relações de trato sucessivo contra a Fazenda, a prescrição do fundo de direito depende de negativa "
              "expressa do direito, em ato concreto ou formal, com ciência do servidor; a simples inércia não inicia "
              "o prazo.",
              '"Tema 1410" STJ prescrição fundo de direito negativa expressa', stj(1410),
              "Sem negativa, prescrevem só as parcelas anteriores aos cinco anos do ajuizamento (Súmula 85/STJ)."),
        ], lacunas="N2 e N3: sem precedente verificado além do citado no alerta."),
    sub("responsabilidade-estado", "Responsabilidade civil do Estado",
        [r"estado", r"prefeitura", r"municipio", r"poder publico", r"policia", r"viatura", r"hospital publico",
         r"\bsus\b", r"preso", r"presidio", r"agente publico", r"buraco", r"servidor causou"],
        [
            p("STF, Tema 940 (RE 1.027.633)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 14/12/2019",
              "Processe o Estado, não o servidor",
              "O dano foi causado por um servidor público no exercício da função.",
              "A ação por dano causado por agente público deve ser proposta contra o Estado ou a prestadora de "
              "serviço público, não contra o agente, assegurado o regresso em caso de dolo ou culpa.",
              '"Tema 940" STF dupla garantia agente público', stf(940)),
            p("STF, Tema 592 (RE 841.526)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 07/09/2016",
              "Estado responde pela morte de preso",
              "Um familiar do cliente morreu enquanto estava preso.",
              "Descumprido o dever específico de proteção (Constituição, art. 5º, XLIX), o Estado é responsável pela "
              "morte do detento.",
              '"Tema 592" STF morte de detento responsabilidade', stf(592)),
            p("STF, Tema 1055 (RE 1.209.429)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 19/11/2021",
              "Jornalista ferido pela polícia em manifestação",
              "O cliente, profissional de imprensa, foi ferido por policiais cobrindo um protesto.",
              "É objetiva a responsabilidade do Estado pelo profissional de imprensa ferido por policiais em "
              "manifestação com tumulto; exclui-se se ele descumpriu advertência ostensiva sobre área de grave risco.",
              '"Tema 1055" STF jornalista ferido manifestação', stf(1055)),
        ], lacunas="N2 e N3: sem precedente verificado."),
    sub("improbidade", "Improbidade administrativa",
        [r"improbidade", r"8\.429", r"14\.230", r"ressarcimento ao erario", r"enriquecimento ilicito",
         r"prefeito", r"vereador", r"gestor", r"licitacao"],
        [
            p("STF, Tema 1199 (ARE 843.989)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 16/02/2023",
              "Improbidade exige dolo; a lei nova retroage em parte",
              "O cliente responde por improbidade por um ato culposo, ainda sem condenação definitiva.",
              "É preciso dolo nos arts. 9º, 10 e 11 da LIA. A revogação da forma culposa não atinge coisa julgada, "
              "mas se aplica aos atos culposos sem condenação transitada; o novo regime de prescrição é irretroativo.",
              '"Tema 1199" STF improbidade dolo retroatividade 14.230', stf(1199)),
            p("STF, Tema 897 (RE 852.475)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 06/12/2019",
              "Ressarcimento por ato doloso é imprescritível",
              "O ente cobra devolução de valores por ato de improbidade antigo.",
              "São imprescritíveis as ações de ressarcimento ao erário fundadas em ato doloso tipificado na Lei de "
              "Improbidade.",
              '"Tema 897" STF imprescritibilidade ressarcimento doloso', stf(897),
              "Para a defesa: sem dolo provado, a imprescritibilidade não se aplica."),
            p("STJ, Tema 1108", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Contratação temporária com base em lei local não é improbidade",
              "O gestor contratou temporários sem concurso, amparado em lei municipal.",
              "A contratação temporária sem concurso, baseada em lei local, por si só não configura improbidade do "
              "art. 11 da LIA, por falta de dolo.",
              '"Tema 1108" STJ contratação temporária improbidade dolo', stj(1108)),
        ], lacunas="N2 e N3: sem precedente verificado."),
    sub("saude-publica", "Saúde pública: medicamentos e tratamentos pelo SUS",
        [r"medicament", r"remedio", r"\bsus\b", r"tratamento", r"cirurgia", r"leito", r"\buti\b", r"farmacia",
         r"secretaria de saude", r"anvisa", r"conitec"],
        [
            p("STF, Tema 6 (RE 566.471)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 04/10/2025",
              "Remédio fora das listas do SUS: requisitos cumulativos",
              "O médico receitou um remédio que o SUS não fornece.",
              "Em regra, remédio fora das listas do SUS não é concedido judicialmente. Excepcionalmente cabe, com "
              "registro na Anvisa, se o autor provar: negativa administrativa; ilegalidade ou demora da Conitec; "
              "falta de substituto no SUS; eficácia por evidência de alto nível (ensaios randomizados, revisão "
              "sistemática); imprescindibilidade por laudo fundamentado; e incapacidade financeira.",
              '"Tema 6" STF medicamento não incorporado requisitos', stf(6),
              "O juiz deve consultar o NATJUS e não pode decidir só com o laudo do autor: junte estudos científicos."),
            p("STF, Tema 1234 (RE 1.366.243)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 07/03/2025",
              "Competência: Justiça Federal a partir de 210 salários mínimos",
              "O tratamento pedido é muito caro e o cliente não sabe se entra contra a União ou o Estado.",
              "Ações de medicamentos não incorporados (e oncológicos) com registro na Anvisa vão à Justiça Federal "
              "quando o custo anual (PMVG/CMED) for igual ou superior a 210 salários mínimos; abaixo disso, à "
              "Justiça Estadual, com regras de ressarcimento entre os entes.",
              '"Tema 1234" STF medicamentos competência 210 salários', stf(1234),
              "Confira na tese as regras sobre medicamentos de mesmo princípio ativo e sobre ressarcimento."),
            p("STJ, Tema 106", "N1", "tese repetitiva, nacional", "EM ATENÇÃO",
              "anterior aos Temas 6 e 1234/STF, que fixaram requisitos próprios e prevalecem",
              "Requisitos do STJ para medicamento fora do SUS",
              "O cliente pede remédio não incorporado com base em laudo do médico assistente.",
              "Exigia, cumulativamente: laudo fundamentado de imprescindibilidade e de ineficácia dos fármacos do SUS, "
              "incapacidade financeira e registro na Anvisa.",
              '"Tema 106" STJ medicamentos não incorporados requisitos', stj(106),
              "Hoje, siga os requisitos mais rígidos do Tema 6/STF (N1)."),
        ], lacunas="N2 e N3: sem precedente verificado."),
]
