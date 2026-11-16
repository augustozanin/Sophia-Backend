"""Direito Imobiliário: precedentes curados (conferidos em 16/11/2026: STF — página do tema e tese oficial —, STJ —
temas e PDF oficial de súmulas —, lista oficial de IRDRs do TJPR)."""
from .base import p, stf, stj, stj_sumula, sub

TJPR_IRDR = "https://ejud.tjpr.jus.br/web/guest/nugep-irdr-admitidos"

ALCANCE = "regional do TJ indicado (RS, SC ou PR), só para casos que tramitam lá"

SUBAREAS = [
    sub("compra-na-planta", "Compra na planta: atraso, distrato e cobranças da construtora",
        [r"na planta", r"construtora", r"incorporador", r"atras\w* na entrega", r"entrega das chaves", r"distrato",
         r"desist\w* do imovel", r"corretagem", r"\bsati\b", r"juros de obra", r"minha casa,? minha vida",
         r"metragem", r"apartamento menor"],
        [
            p("STJ, Tema 996", "N1", "tese repetitiva, nacional (fixada para o Minha Casa, Minha Vida)", "VIGENTE",
              "trânsito em julgado",
              "Atraso na entrega: aluguel presumido e fim dos juros de obra",
              "A construtora atrasou a entrega do apartamento além do prazo de tolerância.",
              "O contrato deve ter prazo certo de entrega, sem vínculo com o financiamento. Passado o prazo com a "
              "tolerância, o prejuízo é presumido (aluguel mensal de imóvel semelhante até a posse), são ilícitos "
              "os juros de obra e o indexador da construção dá lugar ao IPCA, salvo se mais gravoso.",
              '"Tema 996" STJ atraso entrega imóvel aluguel juros de obra', stj(996),
              "Fixado para o PMCMV; fora dele, use por analogia e cite a distinção."),
            p("STJ, Tema 970", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Cláusula penal por atraso não se soma a lucros cessantes",
              "O contrato prevê multa pelo atraso e o cliente também quer aluguéis perdidos.",
              "A cláusula penal moratória indeniza o atraso e, em regra fixada em valor equivalente ao aluguel, "
              "afasta a cumulação com lucros cessantes.",
              '"Tema 970" STJ cláusula penal moratória lucros cessantes', stj(970),
              "Se a multa só existe contra o comprador, ela vale também contra a construtora (Tema 971/STJ)."),
            p("STJ, Tema 938", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Corretagem e taxa SATI",
              "O cliente pagou corretagem e uma taxa de assessoria ao comprar na planta.",
              "Restituição de corretagem ou SATI prescreve em 3 anos. É válido transferir a corretagem ao comprador "
              "se o valor foi informado com destaque antes; a cobrança de SATI vinculada à promessa é abusiva.",
              '"Tema 938" STJ corretagem SATI prescrição trienal', stj(938)),
            p("STJ, Súmula 543", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Distrato: devolução imediata das parcelas",
              "O cliente quer desistir da compra ou a construtora não entregou.",
              "Na resolução de promessa de compra e venda sob o CDC, as parcelas pagas são restituídas de imediato: "
              "integralmente se a culpa é do vendedor, parcialmente se o comprador deu causa.",
              '"Súmula 543" STJ restituição parcelas promessa compra e venda', stj_sumula(543),
              "Contratos após a Lei 13.786/2018 têm regras próprias de distrato; confira a data do contrato. Juros "
              "da restituição em contratos anteriores: Tema 1002/STJ."),
            p("STJ, Súmula 308", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Hipoteca da construtora não atinge o comprador",
              "O apartamento quitado está hipotecado pela construtora ao banco.",
              "A hipoteca firmada entre a construtora e o agente financeiro não tem eficácia perante os adquirentes.",
              '"Súmula 308" STJ hipoteca construtora adquirente', stj_sumula(308)),
            p("TJPR, IRDR 42", "N3", "IRDR, só no Paraná", "VIGENTE", "transitado em julgado",
              "Metragem menor: um ano para abatimento, dez para indenização (PR)",
              "O imóvel tem área menor que a do contrato, no Paraná.",
              "Complemento de área, resolução ou abatimento por metragem menor: decadência de 1 ano (CC, art. 501). "
              "Indenização por danos: prescrição de 10 anos (art. 205), salvo se coincidir com o abatimento. Vício "
              "aparente só se presume em vagas de garagem e lotes urbanos regulares.",
              '"IRDR 42" TJPR metragem a menor decadência 501', TJPR_IRDR),
        ]),
    sub("alienacao-fiduciaria", "Financiamento com alienação fiduciária e leilão",
        [r"alienacao fiduciaria", r"9\.514", r"financiamento imobiliario", r"leilao", r"consolidacao",
         r"retomad", r"caixa economica", r"parcelas do financiamento", r"perder o imovel"],
        [
            p("STF, Tema 982 (RE 860.631)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 22/02/2024",
              "Execução extrajudicial do imóvel é constitucional",
              "O banco consolidou a propriedade e vai leiloar o imóvel sem processo judicial.",
              "É constitucional a execução extrajudicial da alienação fiduciária de imóvel prevista na Lei 9.514/1997.",
              '"Tema 982" STF execução extrajudicial alienação fiduciária', stf(982),
              "Para a defesa: o foco passa a ser vícios do procedimento (intimação, prazos, preço do leilão)."),
            p("STJ, Tema 1095", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Inadimplência no financiamento fiduciário segue a Lei 9.514",
              "O cliente parou de pagar o financiamento e quer a devolução pelo CDC.",
              "Com alienação fiduciária registrada e devedor em mora, a resolução segue a Lei 9.514/1997, afastando "
              "o CDC.",
              '"Tema 1095" STJ alienação fiduciária Lei 9.514 CDC', stj(1095),
              "Desfavorável ao devedor: a Súmula 543 não se aplica nesse cenário."),
            p("TJPR, IRDR 44", "N3", "IRDR, só no Paraná", "VIGENTE", "mérito julgado",
              "Segundo leilão por preço vil é vedado (PR)",
              "O imóvel foi arrematado no segundo leilão por muito menos que a avaliação, no Paraná.",
              "No segundo leilão extrajudicial, é vedada a arrematação do imóvel em garantia fiduciária por preço "
              "vil, inferior à metade do valor atualizado da avaliação.",
              '"IRDR 44" TJPR leilão extrajudicial preço vil', TJPR_IRDR),
        ], lacunas="N2: sem precedente verificado."),
    sub("locacao-condominio", "Locação, fiança e condomínio",
        [r"alug", r"locac", r"locatari", r"inquilino", r"despejo", r"fiador", r"fianca", r"condomin",
         r"sindic", r"taxa condominial", r"benfeitoria"],
        [
            p("STF, Tema 1127 (RE 1.307.334)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 06/08/2022",
              "Fiador perde o bem de família, também na locação comercial",
              "O cliente foi fiador de aluguel de loja e querem penhorar a casa dele.",
              "É constitucional a penhora do bem de família do fiador de locação residencial ou comercial.",
              '"Tema 1127" STF penhora bem de família fiador locação comercial', stf(1127),
              "Mesmo sentido: Tema 1091/STJ e Súmula 549/STJ. O fiador não responde por aditamento a que não anuiu "
              "(Súmula 214/STJ)."),
            p("STJ, Tema 886", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Quem paga o condomínio: quem tem a posse e o condomínio sabia",
              "O imóvel foi vendido sem registro e o condomínio cobra do antigo dono.",
              "O que define o responsável pelo condomínio é a relação material com o imóvel: imitido na posse o "
              "comprador e ciente o condomínio, o vendedor não responde pelo período da posse do comprador.",
              '"Tema 886" STJ despesas condominiais promissário comprador posse', stj(886)),
            p("STJ, Súmula 335", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Renúncia às benfeitorias no contrato de locação",
              "O inquilino fez reformas e quer ser indenizado ao sair.",
              "É válida, na locação, a cláusula de renúncia à indenização das benfeitorias e ao direito de retenção.",
              '"Súmula 335" STJ locação benfeitorias renúncia', stj_sumula(335),
              "Desfavorável ao inquilino: verifique se o contrato tem a cláusula."),
            p("STJ, Súmula 486", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Único imóvel alugado continua protegido",
              "O devedor aluga seu único imóvel e usa o aluguel para morar ou viver.",
              "É impenhorável o único imóvel residencial do devedor locado a terceiros se a renda é revertida para a "
              "subsistência ou moradia da família.",
              '"Súmula 486" STJ único imóvel locado impenhorável', stj_sumula(486)),
        ], lacunas="N3: sem precedente verificado."),
    sub("usucapiao-regularizacao", "Usucapião e regularização",
        [r"usucapi", r"posse ha", r"moro ha", r"\bposse\b", r"terreno", r"lote", r"regulariza", r"escritura",
         r"matricula", r"contrato de gaveta"],
        [
            p("STF, Tema 815 (RE 422.349)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 11/08/2015",
              "Lote menor que o módulo municipal não impede usucapião especial",
              "O cliente mora há anos num lote pequeno, abaixo do tamanho mínimo da lei municipal.",
              "Preenchidos os requisitos do art. 183 da Constituição, a usucapião especial urbana não pode ser "
              "barrada por lei que fixa módulo urbano mínimo.",
              '"Tema 815" STF usucapião especial urbana módulo', stf(815)),
            p("STJ, Tema 985", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Usucapião extraordinária abaixo do módulo municipal",
              "A área possuída é menor que o lote mínimo do município e o cliente quer a usucapião extraordinária.",
              "A usucapião extraordinária, preenchidos seus requisitos, não pode ser negada porque a área é menor "
              "que o módulo da lei municipal.",
              '"Tema 985" STJ usucapião extraordinária módulo municipal', stj(985)),
            p("TJPR, IRDR 27", "N3", "IRDR, só no Paraná", "VIGENTE", "transitado em julgado",
              "Usucapião continua na vara cível mesmo com o Município (PR)",
              "O Município interveio na usucapião por questão urbanística, no Paraná.",
              "A intervenção do Município na usucapião para defender a ordem urbanística não desloca a competência "
              "das Varas Cíveis para as da Fazenda Pública.",
              '"IRDR 27" TJPR usucapião competência município', TJPR_IRDR),
        ], lacunas="N2: sem precedente verificado (a Súmula 11/STJ trata de competência com a União)."),
]
