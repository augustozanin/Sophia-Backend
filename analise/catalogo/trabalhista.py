"""Direito do Trabalho: precedentes curados (conferidos em 16/11/2026: STF — página do tema e tese oficial —; TST —
lista oficial de temas repetitivos e reafirmações publicada pelo TRT3, já que o portal do TST bloqueia acesso
automatizado —; súmulas do TRT4 no portal oficial).

Níveis nesta área: N1 = STF (repercussão geral) e TST (recursos repetitivos e reafirmação de jurisprudência,
vinculantes na Justiça do Trabalho); N2 = súmulas e OJs do TST; N3 = TRTs da 4ª, 9ª e 12ª Regiões."""
from .base import p, stf, sub

TST_TEMAS = ("https://portal.trt3.jus.br/internet/jurisprudencia/incidentes-suscitados-irr-iac-arginc-tst/"
             "casos-repetitivos-tst")
TRT4_SUMULAS = "https://www.trt4.jus.br/portais/trt4/sumulas"

ALCANCE = "regional do TRT indicado (4ª Região/RS, 9ª/PR ou 12ª/SC), só para casos que tramitam lá"

SUBAREAS = [
    sub("vinculo-terceirizacao", "Vínculo de emprego, pejotização, terceirização e aplicativos",
        [r"vinculo", r"carteira assinada", r"sem carteira", r"registro", r"pejotiz", r"\bpj\b", r"\bmei\b",
         r"terceiriz", r"prestador", r"autonom", r"aplicativo", r"\buber\b", r"\bifood\b", r"entregador",
         r"motorista de app"],
        [
            p("STF, Tema 725 (RE 958.252)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 15/10/2024",
              "Terceirização de qualquer atividade é lícita",
              "O cliente trabalhava por uma empresa terceirizada dentro da atividade principal da tomadora.",
              "É lícita a terceirização ou outra divisão do trabalho entre pessoas jurídicas distintas, qualquer que "
              "seja o objeto social, mantida a responsabilidade subsidiária da contratante.",
              '"Tema 725" STF terceirização atividade-fim', stf(725),
              "Fraude com subordinação direta à tomadora continua discutível; prove os fatos concretos."),
            p("STF, Tema 1389 (ARE 1.532.603)", "N1", "repercussão geral reconhecida, mérito pendente",
              "EM ATENÇÃO", "acórdão de repercussão geral publicado em 24/04/2025; sem tese de mérito",
              "Pejotização: competência, ônus da prova e licitude",
              "O cliente trabalhava como PJ ou autônomo, mas com rotina de empregado.",
              "Sem tese ainda. O STF vai decidir a competência (Justiça do Trabalho ou comum), o ônus da prova da "
              "fraude e a licitude da contratação de PJ ou autônomo.",
              '"Tema 1389" STF pejotização suspensão', stf(1389),
              "Houve suspensão nacional dos processos, depois flexibilizada (fontes secundárias: liberação na 1ª e "
              "2ª instâncias em 06/2026). Confira a situação antes de ajuizar."),
            p("STF, Tema 1291 (RE 1.446.336)", "N1", "repercussão geral reconhecida, mérito pendente",
              "EM ATENÇÃO", "acórdão de repercussão geral publicado em 02/07/2024; sem tese de mérito",
              "Motorista de aplicativo: vínculo com a plataforma",
              "O cliente dirige ou entrega por aplicativo e quer o reconhecimento do vínculo.",
              "Sem tese ainda. O STF vai decidir se há vínculo de emprego entre o motorista e a plataforma digital.",
              '"Tema 1291" STF motorista aplicativo vínculo', stf(1291),
              "Não afirme que o STF já negou ou reconheceu o vínculo."),
        ], lacunas="N2 e N3: sem precedente verificado."),
    sub("jornada", "Jornada, horas extras, intervalos e normas coletivas",
        [r"hora[s]? extra", r"jornada", r"cartao de ponto", r"\bponto\b", r"intervalo", r"almoco",
         r"banco de horas", r"compensacao", r"sobreaviso", r"trabalho externo", r"convencao coletiva",
         r"acordo coletivo", r"sindicato"],
        [
            p("STF, Tema 1046 (ARE 1.121.633)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 09/05/2023",
              "Negociado sobre o legislado",
              "A convenção coletiva tirou ou reduziu um direito que a CLT dava ao cliente.",
              "São constitucionais acordos e convenções que, pela adequação setorial negociada, limitam ou afastam "
              "direitos trabalhistas, mesmo sem vantagem compensatória explícita, respeitados os direitos "
              "absolutamente indisponíveis.",
              '"Tema 1046" STF negociado legislado indisponíveis', stf(1046),
              "Para o trabalhador: o caminho é mostrar que o direito afastado é indisponível (saúde, segurança, "
              "patamar mínimo constitucional)."),
            p("TST, Tema 19 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 20/05/2025",
              "Compensação de jornada descaracterizada",
              "Havia acordo de compensação, mas na prática o cliente fazia horas além do combinado.",
              "Descaracterizado o acordo de compensação, deve-se só o adicional sobre as horas até 44 semanais e a "
              "hora cheia com adicional sobre as que passam de 44; a invalidade alcança todo o acordo, não só as "
              "semanas descumpridas.",
              '"Tema 19" TST compensação jornada adicional "Súmula 85"', TST_TEMAS),
            p("TST, Tema 73 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "EM ATENÇÃO",
              "tese fixada; lista oficial indica suspensão no TST, sem trânsito informado",
              "Trabalho externo: a empresa prova que não dava para controlar",
              "O cliente trabalhava na rua e a empresa diz que não precisava pagar horas extras.",
              "É do empregador o ônus de provar a impossibilidade de controle da jornada do trabalho externo, por ser "
              "fato impeditivo do direito do trabalhador.",
              '"Tema 73" TST trabalho externo ônus controle jornada', TST_TEMAS),
            p("TRT4, Súmula 38", "N3", "súmula regional, TRT da 4ª Região", "EM ATENÇÃO",
              "editada em 2004; conflita com o Tema 1046/STF e com o art. 611-A da CLT após 2017",
              "Intervalo reduzido por norma coletiva (RS)",
              "A convenção coletiva reduziu o intervalo de almoço do cliente no RS.",
              "É inválida a cláusula coletiva que suprime ou reduz o intervalo intrajornada sem observar o art. 71, "
              "§ 3º, da CLT.",
              '"Súmula 38" TRT4 intervalo norma coletiva', TRT4_SUMULAS,
              "Útil para fatos anteriores à Lei 13.467/2017; depois, o STF (N1) e o art. 611-A da CLT admitem "
              "redução negociada com mínimo de 30 minutos."),
        ], lacunas="N2: sem precedente verificado."),
    sub("rescisao", "Rescisão, justa causa e verbas rescisórias",
        [r"rescis", r"justa causa", r"demiti", r"demissao", r"dispensad", r"mandad[oa] embora", r"verbas",
         r"\b477\b", r"\b467\b", r"aviso previo", r"rescisao indireta", r"improbidade", r"\btrct\b"],
        [
            p("TST, Tema 85 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 08/05/2025",
              "Horas extras e intervalo sonegados justificam rescisão indireta",
              "A empresa nunca pagou as horas extras nem deu o intervalo, e o cliente quer sair com todos os direitos.",
              "O descumprimento contumaz do pagamento de horas extras e da concessão do intervalo intrajornada "
              "autoriza a rescisão indireta (CLT, art. 483, d).",
              '"Tema 85" TST rescisão indireta horas extras intervalo', TST_TEMAS),
            p("TST, Tema 52 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 05/04/2025",
              "Multa do art. 477 também na rescisão indireta",
              "A rescisão indireta vai ser pedida em juízo e o cliente quer as multas.",
              "Reconhecida em juízo a rescisão indireta, é devida a multa do art. 477, § 8º, da CLT.",
              '"Tema 52" TST multa 477 rescisão indireta', TST_TEMAS),
            p("TST, Tema 62 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 05/04/2025",
              "Justa causa por improbidade revertida gera dano moral",
              "O cliente foi demitido por justa causa acusado de furto ou desonestidade, sem prova.",
              "A reversão da justa causa por improbidade (CLT, art. 482, a) infundada ou não comprovada gera dano "
              "moral in re ipsa.",
              '"Tema 62" TST justa causa improbidade dano moral', TST_TEMAS),
        ], lacunas="N2 e N3: sem precedente verificado."),
    sub("dano-moral-trabalho", "Dano moral no trabalho",
        [r"dano moral", r"assedio", r"humilh", r"constrang", r"xingad", r"carteira retida", r"reteve a carteira",
         r"revista", r"transporte de valores"],
        [
            p("TST, Tema 143 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 13/06/2025",
              "Atraso das verbas rescisórias não gera dano moral sozinho",
              "A empresa não pagou a rescisão no prazo e o cliente quer dano moral por isso.",
              "A ausência ou o atraso na quitação das verbas rescisórias, por si só, não configura dano moral; é "
              "preciso provar lesão concreta a direitos da personalidade.",
              '"Tema 143" TST verbas rescisórias atraso dano moral', TST_TEMAS,
              "Desfavorável ao trabalhador: junte prova do prejuízo concreto (contas atrasadas, negativação)."),
            p("TST, Tema 60 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 05/04/2025",
              "Falta de anotação na carteira não gera dano moral presumido",
              "O cliente trabalhou sem carteira assinada e quer dano moral por isso.",
              "A ausência de anotação do vínculo na carteira não caracteriza dano moral in re ipsa; é preciso provar "
              "constrangimento ou prejuízo.",
              '"Tema 60" TST anotação carteira dano moral', TST_TEMAS),
            p("TRT4, Súmula 82", "N3", "súmula regional, TRT da 4ª Região", "VIGENTE",
              "enunciado no portal oficial do TRT4",
              "Carteira retida gera dano moral (RS)",
              "A empresa ficou com a carteira de trabalho do cliente além do prazo legal.",
              "A retenção injustificada da carteira de trabalho por prazo superior ao dos arts. 29 e 53 da CLT causa "
              "dano moral in re ipsa.",
              '"Súmula 82" TRT4 retenção carteira dano moral', TRT4_SUMULAS),
        ], lacunas="N2: sem precedente verificado."),
    sub("acidente-estabilidade", "Acidente, doença ocupacional e estabilidade (inclusive gestante)",
        [r"acidente", r"doenca ocupacional", r"\bcat\b", r"lesao", r"\bler\b|\bdort\b", r"estabilidade",
         r"gravid", r"gestante", r"gravida", r"licenca[- ]maternidade", r"contrato de experiencia", r"falece"],
        [
            p("TST, Tema 163 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 23/08/2025",
              "Gestante tem estabilidade no contrato de experiência",
              "A cliente engravidou durante o contrato de experiência e foi dispensada no fim dele.",
              "A garantia de emprego da gestante (ADCT, art. 10, II, b) vale no contrato de experiência.",
              '"Tema 163" TST gestante contrato de experiência', TST_TEMAS),
            p("TST, Tema 55 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 05/04/2025",
              "Pedido de demissão da gestante exige assistência sindical",
              "A cliente grávida assinou um pedido de demissão sem o sindicato.",
              "O pedido de demissão da empregada gestante só é válido com assistência do sindicato ou da autoridade "
              "local competente (CLT, art. 500).",
              '"Tema 55" TST pedido de demissão gestante sindicato', TST_TEMAS,
              "Dúvida razoável sobre a data da gravidez não afasta a garantia (Tema 119/TST)."),
            p("TST, Tema 183 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 23/08/2025",
              "Prescrição do acidente conta da consolidação da lesão",
              "O acidente ou a doença aconteceu há tempos, mas a sequela só se firmou recentemente.",
              "O prazo prescricional da reparação por acidente ou doença ocupacional começa na ciência inequívoca da "
              "consolidação da lesão em toda sua extensão.",
              '"Tema 183" TST prescrição acidente consolidação', TST_TEMAS,
              "Morte do trabalhador: família tem dano moral em ricochete por presunção relativa (Tema 181/TST)."),
            p("TRT4, Súmula 91", "N3", "súmula regional, TRT da 4ª Região", "VIGENTE",
              "enunciado no portal oficial do TRT4",
              "Prazo trabalhista para indenização de acidente (RS)",
              "O acidente ocorreu depois de 2004 e o caso tramita no RS.",
              "Aplica-se o prazo do art. 7º, XXIX, da Constituição à indenização por acidente ou doença equiparada "
              "ocorridos após a EC 45/2004.",
              '"Súmula 91" TRT4 prescrição acidente', TRT4_SUMULAS),
        ], lacunas="N2: sem precedente verificado."),
    sub("processo-trabalhista", "Gratuidade, foro e direito intertemporal no processo do trabalho",
        [r"gratuidade", r"justica gratuita", r"custas", r"honorario", r"foro", r"onde entrar", r"outra cidade",
         r"reforma trabalhista", r"13\.467", r"contrato antigo"],
        [
            p("TST, Tema 21 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "tese fixada pelo Pleno; lista oficial do TST (reproduzida pelo TRT3)",
              "Justiça gratuita no processo do trabalho",
              "O cliente ganha um pouco acima do limite e quer justiça gratuita.",
              "O juiz deve conceder de ofício a gratuidade a quem ganha até 40% do teto do RGPS. Acima disso, basta "
              "declaração do interessado (Lei 7.115/1983), sob as penas do art. 299 do CP; impugnada com prova, o "
              "juiz ouve o requerente antes de decidir.",
              '"Tema 21" TST justiça gratuita declaração 40%', TST_TEMAS,
              "Litigância de má-fé não impede a gratuidade (Tema 175/TST)."),
            p("TST, Tema 23 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 29/04/2026",
              "Reforma trabalhista vale para contratos em curso",
              "O contrato começou antes de novembro de 2017 e a empresa cortou direitos depois da reforma.",
              "A Lei 13.467/2017 tem aplicação imediata aos contratos em curso, regulando os direitos legais cujos "
              "fatos geradores ocorreram a partir da sua vigência.",
              '"Tema 23" TST "13.467" contratos em curso', TST_TEMAS,
              "Desfavorável a quem pede direitos suprimidos pela reforma: separe os períodos antes e depois de "
              "11/11/2017."),
            p("TST, Tema 215 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 14/10/2026",
              "Ação no domicílio do trabalhador, excepcionalmente",
              "O cliente mora longe de onde trabalhou e não tem como ir até lá.",
              "Excepcionalmente, a reclamação pode ser proposta no domicílio do trabalhador quando o foro do art. 651 "
              "da CLT inviabilizar ou tornar desproporcional o acesso à Justiça, com fundamentação concreta "
              "(doença, acidente, vulnerabilidade, distância onerosa); hipossuficiência presumida ou só a distância "
              "não bastam.",
              '"Tema 215" TST foro domicílio trabalhador 651', TST_TEMAS),
        ], lacunas="N2 e N3: sem precedente verificado. Correção monetária (ADCs 58 e 59 do STF e Lei "
                   "14.905/2024): não conferido no portal; pesquise antes de calcular."),
    sub("responsabilidade-execucao", "Responsabilidade de tomadores, ente público e grupo econômico",
        [r"subsidiari", r"solidari", r"tomador", r"grupo economico", r"prefeitura", r"orgao publico",
         r"administracao publica", r"execucao", r"socio", r"empresa fechou", r"sucessao"],
        [
            p("STF, Tema 1232 (RE 1.387.795)", "N1", "tese de repercussão geral, nacional", "EM ATENÇÃO",
              "acórdão de mérito publicado em 16/06/2026, sem trânsito em julgado",
              "Grupo econômico: indicar na inicial",
              "A empregadora não pagou e há outras empresas do mesmo grupo com dinheiro.",
              "A execução não pode atingir empresa que não participou da fase de conhecimento: as corresponsáveis, "
              "inclusive do grupo econômico, devem ser indicadas na petição inicial com os requisitos demonstrados. "
              "Exceções: sucessão empresarial e abuso da personalidade jurídica, pelo incidente próprio.",
              '"Tema 1232" STF grupo econômico execução trabalhista', stf(1232),
              "Na inicial, inclua desde já as empresas do grupo e os fatos que provam o grupo."),
            p("STF, Tema 1118 (RE 1.298.647)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 29/04/2025",
              "Terceirização no setor público: o trabalhador prova a culpa",
              "O cliente era terceirizado num órgão público e a prestadora sumiu sem pagar.",
              "Não há responsabilidade subsidiária da Administração só pela inversão do ônus da prova: o "
              "trabalhador deve provar a negligência. Há negligência se o ente ficou inerte após notificação formal "
              "do descumprimento (pelo trabalhador, sindicato, MPT, Defensoria ou outro meio idôneo).",
              '"Tema 1118" STF terceirização administração pública ônus', stf(1118),
              "Oriente o cliente a notificar formalmente o órgão; guarde o comprovante."),
            p("TST, Tema 81 (repetitivo)", "N1", "tese vinculante na Justiça do Trabalho", "VIGENTE",
              "trânsito em julgado em 08/05/2025",
              "Vários tomadores também respondem",
              "O terceirizado trabalhou para várias empresas clientes da prestadora.",
              "A prestação de serviços terceirizados a vários tomadores não afasta a responsabilidade subsidiária "
              "de quem se beneficiou dos serviços.",
              '"Tema 81" TST terceirização pluralidade de tomadores', TST_TEMAS),
        ], lacunas="N2 e N3: sem precedente verificado."),
]
