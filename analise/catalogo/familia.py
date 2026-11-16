"""Família e Sucessões: precedentes curados (conferidos em 16/11/2026: STF — página do tema e tese oficial —,
STJ — temas e PDF oficial de súmulas)."""
from .base import p, stf, stj, stj_sumula, sub

ALCANCE = "regional do TJ indicado (RS, SC ou PR), só para casos que tramitam lá"

SUBAREAS = [
    sub("alimentos", "Alimentos: fixação, revisão e execução",
        [r"alimentos", r"pensao aliment", r"\bpensao\b", r"alimentand", r"alimentante", r"prisao civil",
         r"exonera", r"revisional", r"\bavos?\b", r"maioridade", r"13o|decimo terceiro"],
        [
            p("STJ, Tema 192", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Pensão incide sobre 13º e terço de férias",
              "O alimentante paga pensão em percentual do salário e não desconta sobre o 13º e as férias.",
              "A pensão alimentícia incide sobre o décimo terceiro salário e o terço constitucional de férias.",
              '"Tema 192" STJ pensão "décimo terceiro" férias', stj(192)),
            p("STJ, Súmula 309", "N2", "súmula do STJ, nacional", "VIGENTE",
              "redação alterada pelo STJ; vale o texto atual (PDF oficial)",
              "Prisão civil: as três últimas prestações",
              "O pai ou a mãe deixou de pagar a pensão e o cliente quer a prisão civil.",
              "O débito que autoriza a prisão civil é o das três prestações anteriores ao ajuizamento da execução e "
              "das que vencerem no curso do processo.",
              '"Súmula 309" STJ prisão civil três prestações', stj_sumula(309),
              "Débito mais antigo segue pelo rito da penhora (CPC, art. 528, § 8º). O MP pode propor alimentos para "
              "criança ou adolescente (Súmula 594/STJ)."),
            p("STJ, Súmula 621", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Revisão retroage à citação",
              "O cliente pede para reduzir, aumentar ou extinguir a pensão.",
              "Os efeitos da sentença que reduz, majora ou exonera o alimentante retroagem à data da citação, vedadas "
              "a compensação e a repetição do que foi pago.",
              '"Súmula 621" STJ alimentos retroagem citação', stj_sumula(621),
              "Maioridade não extingue a pensão sozinha: exige decisão judicial com contraditório (Súmula 358/STJ). "
              "Avós só respondem de forma complementar e subsidiária (Súmula 596/STJ)."),
        ], lacunas="N3: sem precedente verificado."),
    sub("uniao-estavel-sucessao", "União estável, regime de bens e sucessão",
        [r"uniao estavel", r"companheir", r"regime de bens", r"separacao obrigatoria", r"70 anos|setenta anos",
         r"septuagenari", r"heranc", r"herdeir", r"inventari", r"partilha", r"testament", r"falece", r"espolio"],
        [
            p("STF, Tema 809 (RE 878.694)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 04/12/2018",
              "Companheiro herda como cônjuge",
              "O companheiro morreu e os parentes dele dizem que o cliente, que vivia em união estável, herda menos.",
              "É inconstitucional a distinção entre cônjuge e companheiro do art. 1.790 do Código Civil; aplica-se "
              "aos dois o regime sucessório do art. 1.829.",
              '"Tema 809" STF companheiro sucessão "1.790"', stf(809),
              "A mesma tese vale para a união homoafetiva (Tema 498/STF)."),
            p("STF, Tema 1236 (ARE 1.309.642)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 10/04/2024",
              "Maiores de 70 anos podem afastar a separação obrigatória",
              "O casal se uniu quando um deles já tinha mais de 70 anos e quer outro regime de bens.",
              "No casamento e na união estável de pessoa maior de 70 anos, o regime de separação do art. 1.641, II, "
              "do Código Civil pode ser afastado por manifestação expressa das partes em escritura pública.",
              '"Tema 1236" STF "maior de 70 anos" separação de bens', stf(1236)),
            p("STJ, Súmula 655", "N2", "súmula do STJ, nacional", "EM ATENÇÃO",
              "anterior ao Tema 1236/STF, que permitiu afastar a separação por escritura pública",
              "União estável de septuagenário: separação obrigatória",
              "A união estável começou depois dos 70 anos e não há escritura escolhendo outro regime.",
              "Na união estável contraída por septuagenário vale a separação obrigatória, comunicando-se os bens "
              "adquiridos na constância quando comprovado o esforço comum.",
              '"Súmula 655" STJ septuagenário "esforço comum"', stj_sumula(655),
              "Se houver escritura pública afastando a separação, prevalece o Tema 1236/STF (N1)."),
        ], lacunas="N3: sem precedente verificado."),
    sub("divorcio-filiacao", "Divórcio, filiação e paternidade",
        [r"divorci", r"separacao judicial", r"separad", r"paternidade", r"\bdna\b", r"investigacao de",
         r"socioafetiv", r"pai biologico", r"multiparental", r"reconhecimento de filho", r"registro de nascimento"],
        [
            p("STF, Tema 1053 (RE 1.167.478)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 16/03/2024",
              "Divórcio sem separação prévia",
              "O cliente quer se divorciar e ouviu que precisaria se separar antes.",
              "Após a EC 66/2010, a separação judicial não é requisito para o divórcio nem subsiste como figura "
              "autônoma; preserva-se o estado civil de quem já estava separado.",
              '"Tema 1053" STF "separação judicial" divórcio', stf(1053),
              "O divórcio pode ser decretado sem prévia partilha dos bens (Súmula 197/STJ)."),
            p("STF, Tema 622 (RE 898.060)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 06/06/2019",
              "Pai socioafetivo e pai biológico ao mesmo tempo",
              "A criança foi criada por um pai, mas o pai biológico é outro, e o cliente quer o reconhecimento.",
              "A paternidade socioafetiva, registrada ou não, não impede o reconhecimento concomitante do vínculo "
              "biológico, com os efeitos jurídicos próprios.",
              '"Tema 622" STF socioafetiva biológica concomitante', stf(622)),
            p("STJ, Súmula 301", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Recusa ao DNA presume a paternidade",
              "O suposto pai se recusa a fazer o exame de DNA.",
              "Na investigação de paternidade, a recusa do suposto pai ao exame de DNA induz presunção relativa de "
              "paternidade.",
              '"Súmula 301" STJ recusa DNA presunção', stj_sumula(301)),
            p("STJ, Súmula 277", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Alimentos desde a citação na investigação",
              "A paternidade foi reconhecida e o cliente quer alimentos atrasados.",
              "Julgada procedente a investigação de paternidade, os alimentos são devidos a partir da citação.",
              '"Súmula 277" STJ investigação paternidade alimentos citação', stj_sumula(277)),
        ], lacunas="N3: sem precedente verificado. Guarda e convivência: sem tese vinculante verificada."),
]
