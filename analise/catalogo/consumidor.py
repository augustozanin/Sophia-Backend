"""Direito do Consumidor: precedentes curados (conferidos em 15/11/2026: STF, STJ e notícias oficiais do STF).

Níveis nesta área: N1 = STF (repercussão geral e controle concentrado) e STJ (repetitivos); N2 = súmulas do STJ
(CPC, art. 927, IV); N3 = TJs de RS, SC e PR."""
from .base import p, stf, stj, stj_sumula, sub

VERIFICADO = "15/11/2026"
ALCANCE = "regional do TJ indicado (RS, SC ou PR), só para casos que tramitam lá"

STF_ADI_7265 = ("https://noticias.stf.jus.br/postsnoticias/"
                "stf-fixa-criterios-para-que-planos-de-saude-cubram-tratamentos-fora-da-lista-da-ans/")
STF_INFO_1214 = "https://www.stf.jus.br/arquivo/informativo/documento/informativo1214.htm"

SUBAREAS = [
    sub("fraudes-bancarias", "Bancos: fraude, golpe e contratação não reconhecida",
         [r"fraude", r"golpe", r"\bpix\b", r"falsa central", r"clonad", r"nao contratei", r"nao reconhec",
          r"no meu nome", r"assinatura", r"\brmc\b", r"\brcc\b", r"cartao consignado", r"margem consign",
          r"emprestimo"],
         [
             p("STJ, Tema 466", "N1", "tese repetitiva, nacional (originou a Súmula 479/STJ)", "VIGENTE",
                "trânsito em julgado",
                "Fraude de terceiro é fortuito interno do banco",
                "Abriram conta ou fizeram empréstimo no nome do cliente, ou ele caiu num golpe e o banco não "
                "devolveu.",
                "Instituições financeiras respondem objetivamente pelos danos de fortuito interno ligados a "
                "fraudes e delitos de terceiros em operações bancárias.",
                '"Tema 466" STJ "fortuito interno" fraude banco', stj(466),
                "Golpes por engenharia social (falsa central, Pix) são decididos caso a caso (falha de "
                "segurança do banco versus culpa exclusiva da vítima); não há tese repetitiva específica."),
             p("STJ, Tema 1061", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Assinatura contestada: o banco prova",
                "O banco diz que o cliente assinou o contrato, mas a assinatura não é dele.",
                "Se o consumidor impugna a autenticidade da assinatura no contrato juntado pelo banco, cabe ao "
                "banco provar que é autêntica (CPC, arts. 6º, 369 e 429, II).",
                '"Tema 1061" STJ assinatura "ônus" banco', stj(1061)),
             p("STJ, Tema 1414", "N1", "tema repetitivo afetado, ainda sem tese", "EM ATENÇÃO",
                "afetado em 2026; sem julgamento; recursos especiais sobre o tema suspensos",
                "Cartão consignado (RMC/RCC): validade, abuso e prazo",
                "Achava que tinha feito empréstimo consignado, mas era cartão, e o desconto nunca acaba.",
                "Sem tese ainda. O STJ vai decidir se vale a decadência do art. 178 do Código Civil ou se há "
                "nulidade sem prazo, e fixar parâmetros objetivos de validade e de abuso. Absorveu o Tema 1328 "
                "(dano moral presumido), que foi cancelado.",
                '"Tema 1414" STJ "cartão de crédito consignado" RMC', stj(1414),
                "Não afirme o resultado. A MP 1.355/2026 prevê a extinção gradual do RMC e do RCC no INSS "
                "(confira o texto oficial)."),
             p("TJSC, IRDR Tema 26", "N3", "IRDR, só em Santa Catarina", "EM ATENÇÃO",
                "tese levada ao STJ (recurso especial em IRDR, hoje no Tema 1414)",
                "RMC anulado não gera dano moral presumido (SC)",
                "O contrato de cartão consignado foi anulado e o cliente quer dano moral.",
                "Segundo fontes secundárias, a invalidação do contrato de cartão com RMC não gera dano moral "
                "presumido.",
                '"IRDR 26" TJSC RMC "dano moral"', stj(1328),
                "Pendente no STJ (Tema 1414). Não trate como definitivo."),
         ]),
    sub("contratos-bancarios", "Contratos bancários: juros, descontos e atendimento",
         [r"juros", r"revisional", r"\btaxa", r"financiament", r"desconto", r"conta[- ]salario", r"salario",
          r"\bfila\b", r"espera", r"atendimento bancario", r"tarifa"],
         [
             p("STJ, Tema 27 (REsp 1.061.530/RS)", "N1", "tese repetitiva, nacional", "VIGENTE",
                "trânsito em julgado em 13/05/2010",
                "Revisão de juros remuneratórios",
                "Os juros do empréstimo, do financiamento ou do cartão são altíssimos.",
                "A revisão dos juros remuneratórios só cabe em situações excepcionais, com relação de consumo "
                "e abusividade cabalmente demonstrada no caso concreto (CDC, art. 51, § 1º).",
                '"Tema 27" STJ "juros remuneratórios" abusividade "taxa média"', stj(27),
                "A comparação com a taxa média do Banco Central para a operação é o parâmetro usual "
                "(orientação do mesmo julgamento, conferida em fontes secundárias)."),
             p("STJ, Tema 1085", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Desconto de empréstimo comum na conta-salário",
                "O banco desconta da conta onde cai o salário quase tudo o que entra.",
                "São lícitos os descontos de empréstimos comuns em conta-corrente, mesmo a que recebe salário, "
                "se autorizados e enquanto durar a autorização; não se aplica por analogia o limite de 30% do "
                "consignado (Lei 10.820/2003).",
                '"Tema 1085" STJ desconto "conta-corrente" 30%', stj(1085),
                "Em superendividamento, veja a sub-área própria."),
             p("STJ, Tema 1156", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Demora no atendimento bancário",
                "Ficou mais tempo na fila do banco do que a lei municipal permite.",
                "O simples descumprimento do prazo legal para atendimento bancário não gera, por si só, dano "
                "moral presumido.",
                '"Tema 1156" STJ fila banco "dano moral"', stj(1156)),
         ], lacunas="N2 e N3: sem precedente verificado."),
    sub("superendividamento", "Superendividamento e mínimo existencial",
         [r"superendivid", r"minimo existencial", r"muitas dividas", r"nao consig\w* pagar", r"renegoci",
          r"repactua"],
         [
             p("STF, ADPFs 1.005, 1.006 e 1.097", "N1", "controle concentrado, eficácia geral", "EM ATENÇÃO",
                "julgadas em 23/04/2026 (Informativo 1214); trânsito em julgado não conferido",
                "Mínimo existencial de R$ 600 e consignado",
                "O cliente tem várias dívidas e o que sobra do salário não paga o básico.",
                "É constitucional fixar por decreto o valor do mínimo existencial (Decreto 11.150/2022, "
                "R$ 600), com reavaliações periódicas baseadas em estudos técnicos. É inconstitucional excluir "
                "o crédito consignado do cálculo.",
                'ADPF 1005 1006 1097 "mínimo existencial" STF', STF_INFO_1214,
                "Use com a Lei 14.181/2021 (CDC, arts. 104-A a 104-C)."),
         ], lacunas="N2 e N3: sem precedente verificado."),
    sub("planos-de-saude", "Planos de saúde",
         [r"plano de saude", r"convenio", r"operadora", r"unimed", r"cobertura", r"\brol\b", r"\bans\b",
          r"cirurgia", r"tratamento", r"medicament", r"internac", r"mensalidade", r"faixa etaria",
          r"home care", r"terapia", r"bariatric", r"carencia", r"preexistent"],
         [
             p("STF, ADI 7.265", "N1", "controle concentrado, eficácia geral", "VIGENTE",
                "julgada em 18/09/2025",
                "Cobertura fora do rol da ANS: cinco critérios cumulativos",
                "O plano negou porque o tratamento não está no rol da ANS.",
                "A Lei 14.454/2022 é válida com interpretação conforme: o plano cobre tratamento fora do rol se, "
                "ao mesmo tempo, (1) há prescrição do médico ou odontólogo assistente; (2) não houve negativa "
                "expressa nem há análise pendente na ANS; (3) não há alternativa adequada no rol; (4) há "
                "comprovação científica de eficácia e segurança; (5) há registro na Anvisa.",
                '"ADI 7265" STF rol ANS critérios', STF_ADI_7265),
             p("STJ, Tema 1082", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Cancelamento de plano coletivo durante tratamento",
                "A operadora cancelou o plano coletivo no meio de um tratamento grave.",
                "Mesmo após rescisão unilateral regular de plano coletivo, a operadora deve manter a assistência "
                "a quem está internado ou em tratamento que garanta a sobrevivência ou a incolumidade, até a "
                "alta, se o titular pagar integralmente a mensalidade.",
                '"Tema 1082" STJ cancelamento plano coletivo tratamento', stj(1082)),
             p("STJ, Tema 952", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
                "Reajuste por faixa etária",
                "Mudou de faixa etária (por exemplo, aos 59 anos) e a mensalidade disparou.",
                "O reajuste por faixa etária em plano individual ou familiar é válido se previsto no contrato, "
                "conforme as normas da ANS e sem percentuais desarrazoados ou aleatórios, sem base atuarial, "
                "que onerem excessivamente ou discriminem o idoso.",
                '"Tema 952" STJ reajuste "faixa etária"', stj(952),
                "Planos coletivos: o Tema 1016/STJ estende essas teses (sem CDC na autogestão) e define a "
                '"variação acumulada"; acórdão publicado, recurso extraordinário pendente.'),
             p("STJ, Súmula 608", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor",
                "CDC nos planos de saúde, salvo autogestão",
                "Plano de empresa, sindicato ou associação que administra o próprio plano.",
                "Aplica-se o CDC aos contratos de plano de saúde, salvo os administrados por entidades de "
                "autogestão.",
                '"Súmula 608" STJ autogestão', stj_sumula(608)),
             p("STJ, Súmula 597", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor",
                "Carência em urgência e emergência",
                "Negaram atendimento de urgência porque o plano estava em carência.",
                "É abusiva a cláusula que prevê carência para urgência ou emergência acima de 24 horas da "
                "contratação.",
                '"Súmula 597" STJ carência urgência', stj_sumula(597)),
         ], lacunas="N3: sem precedente verificado."),
    sub("negativacao-cobranca", "Negativação e cobrança indevida",
         [r"negativ", r"serasa", r"\bspc\b", r"nome sujo", r"cadastro", r"protest", r"cobranc\w* indevid",
          r"cobrara?m", r"nao devo", r"em dobro", r"devolu", r"fatura", r"conta de luz", r"telefon"],
         [
             p("STJ, Tema 929", "N1", "tese repetitiva, nacional", "EM ATENÇÃO",
                "julgado em 15/09/2026, acórdão publicado em 03/11/2026, sem trânsito em julgado",
                "Devolução em dobro (CDC, art. 42)",
                "Cobraram algo que o cliente não devia, e ele pagou.",
                "A devolução em dobro independe de má-fé e cabe quando a cobrança contraria a boa-fé objetiva. "
                "Recusa ou omissão do fornecedor diante de reclamação prévia é indício suficiente. O fornecedor "
                "deve provar que não agiu de forma desleal ou descuidada. Divergência jurisprudencial ou "
                "cláusula depois anulada configuram engano justificável.",
                '"Tema 929" STJ "repetição em dobro" "boa-fé objetiva"', stj(929),
                "Só sobre o que foi efetivamente pago. Confira se o acórdão manteve a modulação temporal da "
                "Corte Especial (EAREsp 676.608/RS). Fraude que levou à negativação: Tema 466/STJ."),
             p("STJ, Súmula 385", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor",
                "Negativação indevida com anotação anterior legítima",
                "Foi negativado por dívida que não é dele, mas já tinha outro apontamento legítimo.",
                "Havendo inscrição legítima anterior, a anotação irregular não gera dano moral, ressalvado o "
                "direito ao cancelamento.",
                '"Súmula 385" STJ "inscrição legítima"', stj_sumula(385)),
         ], lacunas="N3: sem precedente verificado."),
    sub("transporte-aereo", "Transporte aéreo",
         [r"\bvoo", r"aere[oa]", r"companhia aerea", r"atras", r"cancelad", r"bagagem", r"\bmala\b",
          r"extravi", r"overbooking", r"embarque", r"conexao", r"passagem", r"aeroporto"],
         [
             p("STF, Tema 210 (RE 636.331)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 13/12/2022",
                "Voo internacional: danos materiais pelas convenções",
                "A mala sumiu ou houve prejuízo material num voo internacional.",
                "Pelo art. 178 da Constituição, as Convenções de Varsóvia e de Montreal, que limitam a "
                "responsabilidade das transportadoras, prevalecem sobre o CDC quanto aos danos materiais.",
                '"Tema 210" STF Montreal "danos materiais"', stf(210)),
             p("STF, Tema 1240 (RE 1.394.401)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
                "trânsito em julgado em 05/08/2023",
                "Voo internacional: dano moral fora das convenções",
                "Teve transtorno grave num voo internacional e quer dano moral.",
                "As Convenções de Varsóvia e de Montreal não se aplicam aos danos extrapatrimoniais do "
                "transporte aéreo internacional, que seguem o CDC.",
                '"Tema 1240" STF "danos extrapatrimoniais" Montreal', stf(1240)),
             p("STF, Tema 1417 (ARE 1.560.244)", "N1", "repercussão geral reconhecida, mérito pendente",
                "EM ATENÇÃO", "acórdão de repercussão geral publicado em 29/08/2025; sem tese de mérito",
                "Atraso ou cancelamento por caso fortuito ou força maior: CBA ou CDC",
                "O voo foi cancelado ou atrasou por mau tempo ou problema alheio à companhia.",
                "Sem tese ainda. O STF vai decidir se as normas do transporte aéreo prevalecem sobre o CDC na "
                "responsabilidade por cancelamento, alteração ou atraso de voo por caso fortuito ou força maior.",
                '"Tema 1417" STF atraso voo "força maior"', stf(1417),
                "Há notícia de suspensão nacional dos processos; confira antes de ajuizar. Dano moral por "
                "atraso, em regra, não é presumido (CBA, art. 251-A; orientação de turmas do STJ, não tese "
                "vinculante)."),
         ], lacunas="N2 e N3: sem precedente verificado."),
]
