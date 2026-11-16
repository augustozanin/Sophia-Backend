"""Direito Empresarial: precedentes curados (conferidos em 16/11/2026: STJ — temas e PDF oficial de súmulas —, lista
oficial de IRDRs do TJPR)."""
from .base import p, stj, stj_sumula, sub

TJPR_IRDR = "https://ejud.tjpr.jus.br/web/guest/nugep-irdr-admitidos"

ALCANCE = "regional do TJ indicado (RS, SC ou PR), só para casos que tramitam lá"

SUBAREAS = [
    sub("recuperacao-falencia", "Recuperação judicial e falência",
        [r"recuperacao judicial", r"recuperanda", r"falenc", r"falid", r"plano de recuperacao",
         r"administrador judicial", r"credor", r"habilitacao de credito", r"11\.101", r"produtor rural"],
        [
            p("STJ, Tema 1051", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Crédito se sujeita à recuperação pelo fato gerador",
              "A dívida com o cliente nasceu antes do pedido de recuperação, mas a sentença veio depois.",
              "Para submissão à recuperação judicial, a existência do crédito é determinada pela data do seu fato "
              "gerador.",
              '"Tema 1051" STJ recuperação judicial fato gerador crédito', stj(1051)),
            p("STJ, Tema 885", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Avalistas e fiadores seguem executáveis",
              "A empresa devedora entrou em recuperação, mas há sócio avalista ou fiador.",
              "A recuperação do devedor principal não suspende nem extingue execuções contra coobrigados, avalistas e "
              "fiadores (Lei 11.101/2005, art. 49, § 1º).",
              '"Tema 885" STJ recuperação judicial coobrigados avalista', stj(885),
              "Mesmo sentido: Súmula 581/STJ."),
            p("STJ, Tema 1391", "N1", "tese repetitiva, nacional", "EM ATENÇÃO",
              "acórdão publicado, sem trânsito em julgado",
              "Condomínio fica fora da recuperação",
              "O condomínio cobra cotas atrasadas de empresa em recuperação judicial.",
              "Débitos condominiais, mesmo anteriores ao pedido, são extraconcursais e podem ser executados no juízo "
              "cível.",
              '"Tema 1391" STJ condomínio extraconcursal recuperação', stj(1391)),
            p("STJ, Súmula 480", "N2", "súmula do STJ, nacional", "VIGENTE", "enunciado em vigor (PDF oficial)",
              "Bens fora do plano não são do juízo da recuperação",
              "O credor quer penhorar um bem da recuperanda que não está no plano.",
              "O juízo da recuperação não é competente para decidir sobre constrição de bens não abrangidos pelo plano.",
              '"Súmula 480" STJ juízo recuperação bens não abrangidos', stj_sumula(480)),
            p("TJPR, IRDR 23", "N3", "IRDR, só no Paraná", "VIGENTE", "transitado em julgado",
              "Certidões fiscais para conceder a recuperação (PR)",
              "A empresa em recuperação no Paraná quer a homologação do plano sem certidões fiscais.",
              "Havendo lei que permita equacionar o passivo tributário, é obrigatória a juntada de certidões "
              "negativas (ou positivas com efeito de negativas) para conceder a recuperação (Lei 11.101, art. 57); "
              "excepcionalmente, o juiz pode dar prazo razoável.",
              '"IRDR 23" TJPR recuperação judicial certidões negativas', TJPR_IRDR),
        ], lacunas="Produtor rural com mais de dois anos de atividade empresarial pode pedir recuperação se inscrito "
                   "na Junta ao pedir (Tema 1145/STJ)."),
    sub("socios-desconsideracao", "Sócios e desconsideração da personalidade jurídica",
        [r"desconsidera", r"\bsocio", r"sociedade", r"empresa fechou", r"encerrou as atividades", r"\bidpj\b",
         r"confusao patrimonial", r"laranja", r"cotas", r"contrato social", r"ltda"],
        [
            p("STJ, Tema 1210", "N1", "tese repetitiva, nacional", "VIGENTE", "trânsito em julgado",
              "Desconsideração exige abuso, não só falta de bens",
              "A empresa devedora fechou ou não tem bens e o credor quer atingir os sócios.",
              "Nas relações civis e empresariais, a desconsideração exige prova de abuso da personalidade (desvio "
              "de finalidade ou confusão patrimonial, CC art. 50); não bastam a falta de bens nem o encerramento "
              "irregular.",
              '"Tema 1210" STJ desconsideração teoria maior encerramento irregular', stj(1210),
              "Em relação de consumo e em execução fiscal as regras são outras (CDC, art. 28; CTN, art. 135)."),
        ], lacunas="N2 e N3: sem precedente verificado."),
]
