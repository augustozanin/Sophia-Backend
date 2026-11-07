"""
Áreas jurídicas do caso e a orientação específica que cada uma acrescenta aos prompts da IA.

Fonte única: `main.py` valida o `legal_area` do caso por `AREAS_JURIDICAS`, o front lista as
áreas pela rota GET /areas e `analysis.py` junta `orientacao_da_area(...)` ao prompt de sistema
da análise, do chat e da minuta.

Cada área é dividida em blocos e cada tarefa usa só os que lhe servem (o limite de tokens por
minuto do Groq gratuito é apertado):

- análise: tudo, menos a orientação de minuta;
- chat: o que examinar, competência, prazos e cautelas;
- minuta: competência, prazos, orientação de minuta e cautelas.

As normas citadas aqui são pontos de partida para a IA conferir, nunca fontes já verificadas do
caso. De propósito, não há número de tema, súmula ou processo: a regra 2 do prompt proíbe número
sem fonte verificada, e um número escrito aqui seria repetido como se fosse.

Área ausente ou desconhecida (casos antigos) devolve orientação vazia: o prompt fica igual ao
genérico de antes.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

TAREFAS = ("analise", "chat", "minuta")

# Títulos dos blocos, na ordem em que entram no prompt.
_TITULOS = {
    "foco": "O QUE EXAMINAR",
    "tribunais": "COMPETÊNCIA E TRIBUNAIS",
    "prazos": "PRAZOS A CONFERIR (aponte o risco; não calcule a data final sem os dados do caso)",
    "perguntas": "PERGUNTAS QUE COSTUMAM FALTAR",
    "documentos": "DOCUMENTOS E PROVAS TÍPICOS",
    "acordo": "SOLUÇÕES CONSENSUAIS",
    "minuta": "ORIENTAÇÃO PARA A MINUTA",
    "cautelas": "CAUTELAS",
}

_BLOCOS_POR_TAREFA = {
    "analise": ("foco", "tribunais", "prazos", "perguntas", "documentos", "acordo", "cautelas"),
    "chat": ("foco", "tribunais", "prazos", "cautelas"),
    "minuta": ("tribunais", "prazos", "minuta", "cautelas"),
}

_CABECALHO = """\
ORIENTAÇÃO DA ÁREA JURÍDICA DO CASO: {nome}
O advogado classificou este caso como {nome}. Use esta orientação para direcionar a resposta. \
Ela complementa as regras inegociáveis acima e não as substitui: as normas citadas aqui são \
pontos de partida a conferir, não fontes verificadas do caso. Cite só as que se aplicam aos fatos \
relatados e nunca crie número de tema, súmula ou processo a partir delas. Se o relato mostrar \
que o caso pertence, no todo ou em parte, a outra área, diga isso e siga os fatos."""

_FECHO_ANALISE = """\
Ao montar o JSON: use as PERGUNTAS em "perguntas_sugeridas" só quando o relato ainda não as \
responde; use os DOCUMENTOS em "necessidades_adicionais" (tipo "documento_faltante" ou "pericia") \
só quando faltam; use as SOLUÇÕES CONSENSUAIS em "possibilidade_de_acordo" só quando o caso \
permite. Se o caso parecer de outra área, registre em "necessidades_adicionais" com tipo "outro". \
Não copie estas listas: escolha e adapte o que serve a este caso concreto."""

_ALIASES = {
    "criminal": "penal",
    "civel": "civil",
    "familia": "familia-sucessoes",
    "sucessoes": "familia-sucessoes",
    "familia_sucessoes": "familia-sucessoes",
    "previdencia": "previdenciario",
    "trabalho": "trabalhista",
    "consumo": "consumidor",
    "imobiliaria": "imobiliario",
}


def _area(id: str, nome: str, descricao: str, grupos_pecas: List[str], **blocos: List[str]) -> Dict[str, Any]:
    faltando = set(_TITULOS) - set(blocos)
    if faltando:
        raise ValueError(f"Área {id} sem os blocos: {sorted(faltando)}")
    return {"id": id, "nome": nome, "descricao": descricao, "grupos_pecas": grupos_pecas, **blocos}


AREAS: List[Dict[str, Any]] = [
    # ------------------------------------------------------------------ Cível
    _area(
        "civil", "Direito Civil",
        "Contratos, obrigações, cobranças, responsabilidade civil e indenizações entre particulares.",
        ["civel", "juizados", "superiores", "extrajudicial"],
        foco=[
            "Natureza da relação: contratual ou extracontratual. Se houver fornecedor e consumidor "
            "final, aponte que o CDC pode se aplicar (área do consumidor), o que muda ônus da prova e prazos.",
            "Responsabilidade civil: conduta, dano, nexo causal e culpa, ou hipótese de responsabilidade "
            "objetiva (Código Civil, arts. 186, 187 e 927). Excludentes: culpa exclusiva, caso fortuito, força maior.",
            "Inadimplemento e mora: quem descumpriu, quando, se houve constituição em mora, cláusula penal, "
            "arras e perdas e danos (Código Civil, arts. 389 a 416).",
            "Danos: materiais (emergentes e lucros cessantes, arts. 402 e 403), morais, estéticos, perda de "
            "uma chance. Separe o que já tem prova do que é só alegação.",
            "Validade do negócio: capacidade, forma, vícios de consentimento (erro, dolo, coação, lesão, "
            "estado de perigo) e simulação.",
            "Correção monetária e juros: confira os índices legais após a Lei 14.905/2024 (Código Civil, "
            "arts. 389 e 406), sem calcular valores que não estejam no caso.",
            "Via processual: procedimento comum, monitória (prova escrita sem título), execução de título "
            "extrajudicial (CPC, art. 784) ou Juizado Especial Cível (até 40 salários mínimos).",
            "Efetividade: há patrimônio do devedor para satisfazer uma condenação?",
        ],
        tribunais=[
            "Justiça Estadual (Vara Cível ou Juizado Especial Cível), recursos ao Tribunal de Justiça.",
            "Tribunal superior de referência: STJ (interpretação de lei federal, temas repetitivos). STF só "
            "com questão constitucional genuína (regra 3).",
        ],
        prazos=[
            "Prescrição geral de 10 anos (Código Civil, art. 205); reparação civil e enriquecimento sem "
            "causa em 3 anos (art. 206, § 3º); dívidas líquidas em instrumento em 5 anos (art. 206, § 5º, I).",
            "Decadência de 4 anos para anular negócio por vício de consentimento (art. 178).",
            "Vícios redibitórios: 30 dias para móvel e 1 ano para imóvel (art. 445).",
            "Prazos processuais em dias úteis (CPC, art. 219).",
        ],
        perguntas=[
            "Existe contrato escrito? Datas de assinatura, vencimento e do descumprimento.",
            "Quais valores foram pagos ou deixaram de ser pagos, e como isso se prova?",
            "A outra parte já foi notificada ou cobrada? Houve resposta ou proposta?",
            "Quais prejuízos concretos o cliente teve e quais gastos pode comprovar?",
            "Há testemunhas? Há conversas por escrito (WhatsApp, e-mail)?",
            "A outra parte tem bens ou renda conhecidos?",
        ],
        documentos=[
            "Contrato, aditivos, recibos, comprovantes de pagamento e transferências.",
            "Conversas e e-mails (de preferência com ata notarial), notificações enviadas e recebidas.",
            "Orçamentos, notas fiscais, fotos, boletim de ocorrência, laudos técnicos.",
            "Perícia quando o dano ou o vício depender de conhecimento técnico.",
        ],
        acordo=[
            "Notificação extrajudicial com proposta, mediação ou conciliação pré-processual.",
            "Audiência de conciliação ou mediação (CPC, art. 334) e termo de acordo extrajudicial, "
            "que pode ser homologado (título executivo).",
        ],
        minuta=[
            "Pedidos certos e determinados (CPC, arts. 322 e 324), com valor da causa conforme CPC, art. 292.",
            "Indique a opção pela audiência de conciliação ou mediação (CPC, art. 319, VII).",
            "Gratuidade de justiça (CPC, art. 98) e tutela de urgência (CPC, art. 300) só se o caso der base.",
            "Valores de dano moral e materiais: use marcador [VALOR] quando o caso não trouxer o número.",
        ],
        cautelas=[
            "Área ampla: não force tese de outra área sem base nos fatos; se houver relação de consumo, "
            "locação, família ou sociedade empresarial, diga isso.",
            "Não prometa valor de indenização nem chance de êxito.",
        ],
    ),
    # ------------------------------------------------------------------ Família e sucessões
    _area(
        "familia-sucessoes", "Família e Sucessões",
        "Divórcio, união estável, guarda, convivência, alimentos, partilha, inventário e testamentos.",
        ["familia", "civel", "superiores", "extrajudicial"],
        foco=[
            "Vínculo: casamento ou união estável (Código Civil, art. 1.723), datas de início e fim, "
            "e regime de bens (comunhão parcial é a regra supletiva, art. 1.640; separação obrigatória, art. 1.641).",
            "Filhos: idades, com quem moram, rotina, escola e saúde. Guarda compartilhada como regra "
            "(art. 1.584, § 2º) e convivência pelo melhor interesse da criança.",
            "Alimentos: necessidade de quem recebe, possibilidade de quem paga e proporcionalidade "
            "(art. 1.694, § 1º); alimentos provisórios (Lei 5.478/1968, art. 4º); gravídicos (Lei 11.804/2008); "
            "revisão e exoneração quando a situação muda.",
            "Execução de alimentos: rito da prisão para as prestações recentes (CPC, art. 528, § 7º) ou da penhora.",
            "Partilha: bens comuns e particulares, datas de aquisição, dívidas do casal, bens em nome de terceiros.",
            "Sinais de violência doméstica (Lei 11.340/2006) ou de alienação parental (Lei 12.318/2010).",
            "Sucessões: herdeiros necessários e legítima (arts. 1.845 e 1.846), ordem de vocação (art. 1.829), "
            "testamento, inventário judicial ou extrajudicial (CPC, art. 610).",
            "Paternidade: investigação ou negatória, exame de DNA (Lei 8.560/1992).",
        ],
        tribunais=[
            "Justiça Estadual (Vara de Família e Sucessões), com segredo de justiça (CPC, art. 189, II).",
            "Ministério Público intervém quando há incapaz (CPC, art. 698).",
            "Tribunal superior de referência: STJ; STF só com questão constitucional genuína.",
        ],
        prazos=[
            "Abertura do inventário em até 2 meses do óbito (CPC, art. 611); confira a multa estadual do ITCMD.",
            "Divórcio não tem prazo mínimo de casamento (Constituição, art. 226, § 6º).",
            "Prestações alimentares prescrevem em 2 anos a partir do vencimento (Código Civil, art. 206, § 2º), "
            "mas não corre prescrição entre ascendentes e descendentes durante o poder familiar (art. 197, II).",
        ],
        perguntas=[
            "Data do casamento ou do início da união, e data da separação de fato.",
            "Há pacto antenupcial ou escritura de união estável?",
            "Quais bens foram adquiridos, quando e em nome de quem? Há dívidas do casal?",
            "Renda de cada genitor e despesas mensais do filho (escola, saúde, moradia, alimentação).",
            "Como é hoje a convivência com o outro genitor? Há acordo possível?",
            "Houve violência, ameaça ou medida protetiva?",
            "No inventário: data do óbito, último domicílio, herdeiros, bens, dívidas e testamento.",
        ],
        documentos=[
            "Certidões de casamento, nascimento e óbito atualizadas; pacto antenupcial ou escritura de união estável.",
            "Matrículas de imóveis, documentos de veículos, extratos, declarações de imposto de renda.",
            "Holerites e comprovantes das despesas do filho; sinais exteriores de riqueza do alimentante.",
            "Boletim de ocorrência e decisão de medida protetiva, se houver.",
            "Estudo psicossocial quando a guarda for disputada.",
        ],
        acordo=[
            "Mediação familiar (CPC, art. 694) e acordo sobre guarda, convivência e alimentos.",
            "Divórcio e inventário extrajudiciais em cartório quando cabíveis: confira os requisitos atuais "
            "do CPC (arts. 610 e 733) e das normas do CNJ, inclusive havendo filhos menores ou incapazes.",
        ],
        minuta=[
            "Peça em segredo de justiça; peça a intimação do Ministério Público quando houver incapaz.",
            "Alimentos: separe provisórios e definitivos e indique o valor ou percentual pedido com marcador "
            "[VALOR] se o caso não trouxer o número.",
            "Guarda: descreva o regime de convivência proposto (dias, férias, datas comemorativas).",
            "Partilha: liste os bens com marcadores para dados faltantes ([MATRÍCULA], [PLACA]).",
        ],
        cautelas=[
            "Linguagem cuidadosa: é conflito pessoal e muitas vezes envolve crianças.",
            "Havendo sinal de violência doméstica, priorize a proteção (medidas protetivas) antes de outras teses.",
        ],
    ),
    # ------------------------------------------------------------------ Trabalhista
    _area(
        "trabalhista", "Direito do Trabalho",
        "Vínculo de emprego, verbas rescisórias, jornada, adicionais, acidentes e assédio.",
        ["trabalhista", "extrajudicial"],
        foco=[
            "Quem é o cliente: trabalhador ou empregador. A análise muda de lado, não de critério.",
            "Vínculo de emprego: pessoalidade, onerosidade, não eventualidade e subordinação (CLT, arts. 2º e 3º); "
            "pejotização, informalidade, terceirização (Lei 6.019/1974) e grupo econômico (CLT, art. 2º, § 2º).",
            "Forma de saída: sem justa causa, justa causa (art. 482), rescisão indireta (art. 483), pedido de "
            "demissão ou acordo (art. 484-A). Verbas devidas em cada uma, multas dos arts. 477, § 8º, e 467.",
            "Jornada: horas extras, controle de ponto (art. 74, § 2º), intervalos (art. 71, § 4º), trabalho em "
            "domingos e feriados, sobreaviso.",
            "Adicionais de insalubridade e periculosidade (perícia obrigatória, art. 195), adicional noturno, "
            "equiparação salarial (art. 461), salário por fora.",
            "Acidente de trabalho e doença ocupacional: CAT, afastamento, estabilidade de 12 meses (Lei 8.213/1991, "
            "art. 118), indenizações. Estabilidade da gestante (ADCT, art. 10, II, b).",
            "Assédio moral ou sexual e dano extrapatrimonial (CLT, arts. 223-A a 223-G).",
            "FGTS e multa de 40%, seguro-desemprego, guias.",
            "Custo do processo para o trabalhador: honorários de sucumbência (art. 791-A) e requisitos da justiça "
            "gratuita (art. 790, §§ 3º e 4º).",
        ],
        tribunais=[
            "Justiça do Trabalho (Constituição, art. 114): Vara do Trabalho, TRT e TST.",
            "Nesta área a regra 3 se lê assim: o tribunal superior de referência é o TST; STF só em questão "
            "constitucional. Em \"temas_stf_stj\" cabem também súmulas, orientações jurisprudenciais e "
            "incidentes de recursos repetitivos do TST, sob as mesmas regras de fonte.",
        ],
        prazos=[
            "Prescrição de 5 anos durante o contrato, limitada a 2 anos após o fim (Constituição, art. 7º, XXIX). "
            "Se o contrato acabou há perto de 2 anos, isso é urgente.",
            "Prescrição do FGTS: confira o entendimento atual do STF e a modulação aplicável.",
            "Recursos em 8 dias (CLT, art. 895); embargos de declaração em 5 dias (art. 897-A).",
        ],
        perguntas=[
            "Datas de admissão e de saída; a carteira foi assinada desde o início?",
            "Função real, salário registrado e valores pagos por fora.",
            "Jornada real (entrada, saída, intervalo) e se o ponto registrava a jornada verdadeira.",
            "Ambiente com agentes insalubres ou perigosos? Recebia EPI?",
            "Motivo e forma da saída; recebeu as verbas, as guias do FGTS e do seguro-desemprego?",
            "Houve acidente, doença, afastamento pelo INSS ou gravidez no período?",
            "Há testemunhas (colegas que já saíram da empresa) e mensagens da chefia?",
            "A empresa segue funcionando? Há outras empresas do mesmo grupo ou sócios conhecidos?",
        ],
        documentos=[
            "Carteira de trabalho (física ou digital), contrato, holerites, TRCT, extrato do FGTS.",
            "Cartões de ponto, escalas, mensagens e e-mails da chefia.",
            "Atestados, CAT, exames, comunicações do INSS.",
            "Perícia técnica (insalubridade, periculosidade) ou médica (doença ocupacional) quando houver o pedido.",
            "Se o cliente é a empresa: controles de jornada, recibos assinados, políticas internas, PPRA/PGR e PCMSO.",
        ],
        acordo=[
            "Conciliação é tentada obrigatoriamente em audiência (CLT, arts. 846 e 850).",
            "Acordo extrajudicial homologado na Justiça do Trabalho, com advogados distintos para cada parte "
            "(CLT, arts. 855-B a 855-E).",
        ],
        minuta=[
            "Pedidos líquidos com valor indicado (CLT, art. 840, § 1º). Sem dados para calcular, use marcadores "
            "como [VALOR ESTIMADO] e não invente cálculo.",
            "Cada pedido com seu fato e seu fundamento, na mesma ordem dos pedidos finais.",
            "Justiça gratuita com declaração de hipossuficiência, se cabível.",
            "Contestação: impugne pedido a pedido e alegue prescrição quando houver.",
        ],
        cautelas=[
            "Pedido sem prova pode gerar honorários de sucumbência contra o trabalhador: aponte esse risco.",
            "Não afirme vínculo de emprego sem os quatro requisitos presentes nos fatos.",
        ],
    ),
    # ------------------------------------------------------------------ Previdenciário
    _area(
        "previdenciario", "Direito Previdenciário",
        "Aposentadorias, benefícios por incapacidade, pensão por morte, BPC/LOAS e revisões no INSS.",
        ["previdenciario", "juizados", "civel", "superiores", "extrajudicial"],
        foco=[
            "Benefício pretendido: aposentadoria (programada, especial, da pessoa com deficiência — LC 142/2013, "
            "por incapacidade permanente), auxílio por incapacidade temporária, auxílio-acidente (Lei 8.213/1991, "
            "art. 86), pensão por morte (art. 74), salário-maternidade (art. 71) ou BPC/LOAS (Lei 8.742/1993, art. 20, "
            "assistencial, sem exigir contribuição).",
            "Qualidade de segurado e período de graça (art. 15), carência (arts. 24 a 27) e a data de início da "
            "incapacidade em relação a esses dois requisitos.",
            "Regras da Reforma da Previdência (EC 103/2019): direito adquirido até 13/11/2019 e regras de transição; "
            "compare qual regra dá o melhor benefício.",
            "Tempo de contribuição: vínculos que faltam no CNIS, períodos sem registro, contribuições em atraso, "
            "tempo rural, tempo especial (agentes nocivos, PPP e LTCAT — arts. 57 e 58).",
            "Segurado especial rural (art. 11, VII): exige início de prova material, não só testemunhas (art. 55, § 3º).",
            "BPC: idade de 65 anos ou deficiência de longo prazo, renda familiar por pessoa e sua flexibilização, "
            "avaliação biopsicossocial.",
            "Pensão por morte: qualidade de segurado do falecido, dependência, tempo de união e duração da cota.",
            "Revisões: erro de cálculo, períodos não computados, decadência do direito de revisar.",
        ],
        tribunais=[
            "Justiça Federal (Constituição, art. 109, I); Juizado Especial Federal até 60 salários mínimos "
            "(Lei 10.259/2001, art. 3º), com Turma Recursal, Turma Regional e TNU.",
            "Competência delegada da Justiça Estadual quando a comarca fica a mais de 70 km de vara federal "
            "(Constituição, art. 109, § 3º). Benefício acidentário (acidente de trabalho) é da Justiça Estadual.",
            "Tribunais de referência: TRFs, TNU, STJ e STF. Em \"temas_stf_stj\" cabem também temas da TNU, "
            "sob as mesmas regras de fonte.",
        ],
        prazos=[
            "Decadência de 10 anos para revisar o ato de concessão (Lei 8.213/1991, art. 103).",
            "Prescrição das parcelas vencidas há mais de 5 anos (art. 103, parágrafo único): a ação não "
            "recupera tudo se demorar.",
            "Recurso administrativo ao CRPS em 30 dias da ciência da decisão (Decreto 3.048/1999; confira).",
            "Período de graça em curso: se o cliente está perto de perder a qualidade de segurado, é urgente.",
        ],
        perguntas=[
            "Data de nascimento e histórico completo de trabalho (urbano, rural, com ou sem carteira, autônomo, MEI).",
            "Já pediu o benefício ao INSS? Data do pedido (DER), número do benefício (NB) e motivo do indeferimento.",
            "Trabalhou exposto a ruído, agentes químicos, biológicos ou em atividade perigosa? Em quais períodos?",
            "Doença ou lesão: desde quando, diagnóstico, tratamento, se consegue exercer a profissão habitual.",
            "Recebe ou recebeu outro benefício?",
            "No BPC: quem mora na casa, renda de cada um, despesas com saúde, inscrição no CadÚnico.",
            "Na pensão: data do óbito, vínculo com o falecido e tempo de casamento ou união.",
        ],
        documentos=[
            "CNIS, cópia integral do processo administrativo (Meu INSS) e carta de indeferimento.",
            "Carteiras de trabalho, carnês e guias de contribuição, PPP e LTCAT.",
            "Laudos, atestados, exames e receitas com datas (para fixar o início da incapacidade).",
            "Prova material rural: notas de produtor, ITR, contratos de parceria, certidões com a profissão.",
            "Certidão de óbito e provas da união ou dependência; CadÚnico no BPC.",
            "Perícia médica judicial (incapacidade) e perícia social (BPC), com quesitos.",
        ],
        acordo=[
            "Propostas de acordo do INSS em juízo são comuns em benefícios por incapacidade: compare o valor "
            "proposto com os atrasados devidos antes de recomendar.",
            "Recurso administrativo, novo requerimento com documentos novos ou justificação administrativa.",
        ],
        minuta=[
            "Informe DER, NB e a data de início pretendida (DIB) com marcadores quando faltarem.",
            "Valor da causa: parcelas vencidas mais 12 vincendas (CPC, art. 292, §§ 1º e 2º); no JEF, avalie a "
            "renúncia ao que exceder o teto.",
            "Tutela de urgência pelo caráter alimentar, quando houver prova da probabilidade do direito.",
            "Apresente quesitos para a perícia e peça a juntada da cópia do processo administrativo.",
        ],
        cautelas=[
            "Sem requerimento administrativo prévio, a ação em regra não tem interesse de agir: verifique antes.",
            "Não afirme valor de benefício nem tempo de contribuição sem o CNIS.",
        ],
    ),
    # ------------------------------------------------------------------ Consumidor
    _area(
        "consumidor", "Direito do Consumidor",
        "Produtos e serviços com defeito, cobranças indevidas, negativação, bancos, planos de saúde e voos.",
        ["civel", "juizados", "superiores", "extrajudicial"],
        foco=[
            "Relação de consumo: consumidor e fornecedor (CDC, arts. 2º e 3º), consumidor por equiparação "
            "(arts. 17 e 29). Pessoa jurídica só como destinatária final ou vulnerável.",
            "Fato do produto ou serviço, com dano ao consumidor (arts. 12 e 14), ou vício que torna o produto "
            "inadequado (arts. 18 e 20). A responsabilidade é objetiva e solidária na cadeia (art. 7º, parágrafo único).",
            "Inversão do ônus da prova (art. 6º, VIII): verossimilhança ou hipossuficiência.",
            "Práticas e cláusulas abusivas (arts. 39 e 51), publicidade enganosa (art. 37), venda casada.",
            "Cobrança indevida: repetição em dobro do que foi pago (art. 42, parágrafo único) e seus requisitos.",
            "Negativação: notificação prévia (art. 43, § 2º), dívida inexistente, inscrições anteriores legítimas "
            "que podem afastar o dano moral.",
            "Setores frequentes: bancos e fraudes, planos de saúde (Lei 9.656/1998 e normas da ANS; autogestão "
            "segue outro regime), transporte aéreo (Resolução ANAC 400/2016; dano extrapatrimonial exige prova — "
            "Código Brasileiro de Aeronáutica, art. 251-A; voos internacionais seguem a Convenção de Montreal "
            "para danos materiais), compras pela internet (direito de arrependimento em 7 dias, art. 49; Decreto 7.962/2013).",
            "Superendividamento (Lei 14.181/2021; CDC, arts. 104-A a 104-C).",
            "Dano moral: diferencie mero aborrecimento de lesão comprovável; desvio produtivo do tempo do consumidor.",
        ],
        tribunais=[
            "Justiça Estadual: Juizado Especial Cível (até 40 salários mínimos; sem advogado até 20 — Lei 9.099/1995, "
            "art. 9º) ou Vara Cível, no foro do domicílio do consumidor (CDC, art. 101, I).",
            "Tribunal superior de referência: STJ; STF só com questão constitucional genuína.",
        ],
        prazos=[
            "Reclamar de vício aparente: 30 dias (produto não durável) ou 90 dias (durável); vício oculto conta "
            "da descoberta (CDC, art. 26). Reclamação formal ao fornecedor suspende o prazo (art. 26, § 2º).",
            "Reparação por fato do produto ou serviço: 5 anos do conhecimento do dano e da autoria (art. 27).",
        ],
        perguntas=[
            "Data da compra ou contratação, valor e forma de pagamento.",
            "Qual o defeito ou a falha, quando apareceu e o que o fornecedor respondeu?",
            "Há protocolos de atendimento, reclamação no Procon ou no consumidor.gov.br?",
            "Houve negativação? Existem outras negativações em nome do cliente?",
            "Quais prejuízos concretos (gastos extras, compromissos perdidos, tempo gasto tentando resolver)?",
            "O produto foi para assistência técnica? Quantas vezes e por quanto tempo?",
        ],
        documentos=[
            "Nota fiscal, contrato, faturas, comprovantes de pagamento.",
            "Protocolos, e-mails, prints com data, gravações de atendimento.",
            "Extrato de SPC/Serasa e relatório do Registrato (Banco Central).",
            "Ordens de serviço da assistência técnica; laudo técnico ou perícia quando o vício for discutido.",
            "Bilhete aéreo, comunicações da companhia e comprovantes de gastos durante o atraso.",
        ],
        acordo=[
            "SAC e ouvidoria, Procon, consumidor.gov.br (empresas costumam responder com proposta).",
            "Conciliação no Juizado Especial; acordo com retirada da negativação e devolução de valores.",
        ],
        minuta=[
            "Peça a inversão do ônus da prova e a aplicação do CDC de forma fundamentada.",
            "Tutela de urgência para retirar negativação, restabelecer serviço ou autorizar tratamento, se o caso der base.",
            "Repetição em dobro só para valores efetivamente pagos; dano moral com valor em marcador [VALOR] "
            "quando o advogado não informou.",
            "No Juizado, verifique o teto de alçada e a necessidade de perícia complexa (que afasta o JEC).",
        ],
        cautelas=[
            "Não trate todo aborrecimento como dano moral: a jurisprudência é restritiva em vários setores.",
            "Se o caso envolve imóvel na planta, plano de saúde ou fraude digital, combine com essas orientações.",
        ],
    ),
    # ------------------------------------------------------------------ Empresarial
    _area(
        "empresarial", "Direito Empresarial",
        "Sociedades, conflitos entre sócios, contratos empresariais, títulos de crédito e recuperação judicial.",
        ["civel", "superiores", "extrajudicial"],
        foco=[
            "Tipo societário e documentos de base: sociedade limitada (Código Civil, arts. 1.052 a 1.087), "
            "sociedade anônima (Lei 6.404/1976), contrato social, alterações e acordo de sócios.",
            "Conflitos entre sócios: retirada, exclusão (art. 1.085 para a extrajudicial), dissolução parcial e "
            "apuração de haveres (CPC, arts. 599 a 609), deveres do administrador e prestação de contas.",
            "Responsabilidade de sócios e administradores e desconsideração da personalidade jurídica "
            "(Código Civil, art. 50; incidente do CPC, arts. 133 a 137).",
            "Contratos empresariais: paridade e intervenção mínima (Código Civil, art. 421-A), distribuição, "
            "franquia (Lei 13.966/2019), representação comercial (Lei 4.886/1965), fornecimento.",
            "Títulos de crédito: cheque (Lei 7.357/1985), duplicata (Lei 5.474/1968), nota promissória e letra de "
            "câmbio (Decreto 57.663/1966), protesto (Lei 9.492/1997).",
            "Crise da empresa: recuperação judicial ou extrajudicial e falência (Lei 11.101/2005): crédito sujeito "
            "ou não à recuperação (art. 49), suspensão das execuções (art. 6º), habilitação e classificação do crédito.",
            "Propriedade industrial e concorrência desleal (Lei 9.279/1996): marca, nome empresarial, segredo.",
        ],
        tribunais=[
            "Justiça Estadual, em varas empresariais especializadas onde houver; juízo da recuperação ou da "
            "falência para o que for da sua competência.",
            "Verifique cláusula compromissória: se houver, a disputa vai à arbitragem (Lei 9.307/1996).",
            "Tribunal superior de referência: STJ; STF só com questão constitucional genuína.",
        ],
        prazos=[
            "Prescrição cambial dos títulos (cheque: 6 meses após o fim do prazo de apresentação, Lei 7.357/1985, "
            "art. 59) e, depois dela, a via da ação de enriquecimento, monitória ou cobrança.",
            "Habilitação ou divergência de crédito na recuperação: 15 dias do edital (Lei 11.101/2005, art. 7º, § 1º).",
            "Prazos do contrato social e do acordo de sócios para direito de preferência, retirada e pagamento de haveres.",
        ],
        perguntas=[
            "Quem são os sócios, qual a participação de cada um e quem administra?",
            "Há acordo de sócios, cláusula arbitral ou eleição de foro?",
            "Qual a situação financeira da empresa e da outra parte? Alguma está em recuperação judicial?",
            "Quais títulos ou contratos fundamentam a cobrança, com datas e valores?",
            "Houve notificação, protesto ou tentativa de negociação?",
        ],
        documentos=[
            "Contrato social e alterações (Junta Comercial), acordo de sócios, atas e livros.",
            "Balanços e demonstrativos contábeis; perícia contábil na apuração de haveres.",
            "Contratos, títulos, instrumentos de protesto, notificações.",
            "Certidões de distribuição, de falência e recuperação; registros no INPI.",
        ],
        acordo=[
            "Negociação estruturada, mediação empresarial ou arbitragem.",
            "Recuperação extrajudicial ou acordo com credores quando o cliente é a empresa em crise.",
        ],
        minuta=[
            "Antes de ação judicial, confirme que não há cláusula arbitral.",
            "Junte os atos societários e indique o valor da causa conforme o proveito econômico (haveres, crédito).",
            "Na recuperação judicial, identifique se o crédito é concursal ou extraconcursal antes de pedir.",
        ],
        cautelas=[
            "Diferencie a pessoa jurídica dos sócios: não atribua dívida da empresa ao sócio sem base legal.",
            "Se o conflito for de consumo ou trabalhista, a área é outra.",
        ],
    ),
    # ------------------------------------------------------------------ Tributário
    _area(
        "tributario", "Direito Tributário",
        "Cobranças de tributos, autos de infração, execução fiscal, restituição e planejamento tributário.",
        ["tributario", "administrativo", "civel", "superiores", "extrajudicial"],
        foco=[
            "Tributo e ente: federal, estadual ou municipal; espécie (imposto, taxa, contribuição) e período.",
            "Fase: administrativa (lançamento, auto de infração, impugnação) ou judicial (execução fiscal, anulatória, "
            "declaratória, mandado de segurança, repetição de indébito).",
            "Constituição do crédito (CTN, art. 142), decadência (arts. 150, § 4º, e 173) e prescrição (art. 174), "
            "incluindo a intercorrente na execução fiscal (Lei 6.830/1980, art. 40).",
            "Suspensão da exigibilidade (CTN, art. 151) e certidões negativas ou positivas com efeito de negativa "
            "(arts. 205 e 206).",
            "Limitações ao poder de tributar (Constituição, art. 150): legalidade, anterioridade, não confisco.",
            "Responsabilidade de sócios e administradores e redirecionamento da execução fiscal (CTN, art. 135).",
            "Restituição e compensação do que foi pago indevidamente (CTN, arts. 165 a 168; Lei 9.430/1996, art. 74).",
            "Denúncia espontânea (CTN, art. 138), Simples Nacional (LC 123/2006), transação tributária (Lei 13.988/2020).",
            "Reforma do consumo (EC 132/2023 e LC 214/2025): para fatos a partir de 2026, confira as regras de "
            "transição de IBS e CBS.",
        ],
        tribunais=[
            "Tributos federais: Justiça Federal; estaduais e municipais: Justiça Estadual (Vara da Fazenda Pública "
            "ou de execuções fiscais).",
            "Esfera administrativa: CARF (federal) e conselhos e tribunais administrativos estaduais e municipais.",
            "Tribunais superiores: STJ (CTN e lei federal) e STF, porque matéria tributária é muitas vezes "
            "constitucional — aqui a regra 3 não afasta o STF quando a questão constitucional for real.",
        ],
        prazos=[
            "Impugnação no processo administrativo federal: 30 dias da ciência (Decreto 70.235/1972, art. 15).",
            "Embargos à execução fiscal: 30 dias da garantia (Lei 6.830/1980, art. 16).",
            "Repetição de indébito: 5 anos do pagamento (CTN, art. 168; LC 118/2005, art. 3º).",
            "Mandado de segurança: 120 dias da ciência do ato (Lei 12.016/2009, art. 23).",
            "Parcelamento ou confissão interrompem a prescrição (CTN, art. 174, parágrafo único, IV).",
        ],
        perguntas=[
            "Qual tributo, de que período e de que valor? Quem cobra?",
            "Quando o cliente foi notificado do lançamento? Já apresentou impugnação ou recurso?",
            "O débito está inscrito em dívida ativa? Há execução fiscal, citação ou bens penhorados?",
            "Houve parcelamentos anteriores ou adesão a programas de regularização?",
            "Qual o regime tributário da empresa e o que mudou no período?",
            "O cliente precisa de certidão negativa com urgência (licitação, financiamento, venda)?",
        ],
        documentos=[
            "Auto de infração, notificações, cópia do processo administrativo, CDA.",
            "Declarações entregues (DCTF, SPED, GIA, DEFIS), guias pagas, livros fiscais.",
            "Contrato social e alterações; extratos de parcelamento; certidões fiscais.",
            "Perícia contábil quando a base de cálculo for discutida.",
        ],
        acordo=[
            "Transação tributária, parcelamentos, autorregularização e denúncia espontânea.",
            "Negociação com a procuradoria da Fazenda (PGFN, procuradorias estaduais e municipais).",
        ],
        minuta=[
            "Indique o fundamento da suspensão da exigibilidade (depósito, liminar, impugnação) quando pedir CND.",
            "Mandado de segurança só com prova pré-constituída; identifique a autoridade coatora correta.",
            "Embargos à execução fiscal exigem garantia do juízo; exceção de pré-executividade só para matéria "
            "conhecível de ofício sem produção de provas.",
            "Valores do débito em marcador [VALOR] quando não estiverem nos documentos.",
        ],
        cautelas=[
            "Não afirme que um tributo é inconstitucional sem fonte verificada do tribunal que decidiu.",
            "Distinga planejamento lícito de evasão: não sugira ocultar receitas ou patrimônio.",
        ],
    ),
    # ------------------------------------------------------------------ Penal
    _area(
        "penal", "Direito Penal",
        "Defesa criminal, prisões, inquéritos, ações penais, queixa-crime e execução penal.",
        ["penal", "superiores"],
        foco=[
            "Posição do cliente (investigado, réu, preso, vítima ou querelante) e fase (inquérito, denúncia, "
            "instrução, sentença, recurso, execução penal).",
            "Se o cliente está preso, comece pela liberdade: legalidade do flagrante (CPP, art. 302), audiência de "
            "custódia (art. 310), requisitos e fundamentação da preventiva (arts. 312 e 313), revisão a cada 90 dias "
            "(art. 316, parágrafo único), cautelares alternativas (art. 319), prisão domiciliar (arts. 318 e 318-A).",
            "Tipo penal imputado: elementos, dolo ou culpa, tentativa, concurso de pessoas, possível desclassificação.",
            "Nulidades e provas ilícitas (Constituição, art. 5º, LVI; CPP, art. 157): entrada em domicílio sem "
            "mandado (art. 5º, XI), reconhecimento pessoal fora do art. 226 do CPP, quebra da cadeia de custódia "
            "(CPP, arts. 158-A a 158-F), acesso a celular sem autorização, direito ao silêncio (art. 5º, LXIII).",
            "Excludentes de ilicitude (CP, arts. 23 a 25) e de culpabilidade.",
            "Prescrição (CP, arts. 109, 110 e 115 — prazo pela metade para menor de 21 anos na data do fato ou "
            "maior de 70 na sentença).",
            "Pena, se houver condenação: dosimetria (CP, arts. 59 e 68), regime (art. 33), substituição por "
            "restritivas de direitos (art. 44), sursis (art. 77); na execução, progressão (LEP, art. 112) e remição (art. 126).",
            "Leis especiais frequentes: Drogas (Lei 11.343/2006 — uso, art. 28, ou tráfico, art. 33, e tráfico "
            "privilegiado, § 4º) e violência doméstica (Lei 11.340/2006, que afasta a Lei 9.099/1995 — art. 41).",
            "Ação penal: pública incondicionada, condicionada à representação ou privada (CP, art. 100).",
        ],
        tribunais=[
            "Justiça Estadual em regra; Justiça Federal nos casos do art. 109, IV e V, da Constituição; Tribunal do "
            "Júri para crimes dolosos contra a vida; Juizado Especial Criminal para pena máxima de até 2 anos "
            "(Lei 9.099/1995, art. 61).",
            "Tribunais superiores: STJ (habeas corpus, recurso especial) e STF (habeas corpus, recurso extraordinário). "
            "Em matéria penal o STF julga habeas corpus sem ser só questão constitucional; cite precedentes só com fonte verificada.",
        ],
        prazos=[
            "Resposta à acusação: 10 dias da citação (CPP, art. 396).",
            "Apelação: 5 dias para interpor e 8 para as razões (CPP, arts. 593 e 600).",
            "Representação e queixa-crime: decadência em 6 meses do conhecimento da autoria (CP, art. 103; CPP, art. 38).",
            "Prescrição da pretensão punitiva e executória: verifique datas do fato, do recebimento da denúncia e da sentença.",
        ],
        perguntas=[
            "Data, hora e local dos fatos; como foi a abordagem ou a prisão.",
            "Havia mandado? Quem autorizou a entrada na casa? O celular foi acessado e com que autorização?",
            "O cliente foi informado do direito ao silêncio? Houve violência na abordagem?",
            "Como foi feito o reconhecimento (fotos, presencial, com outras pessoas ao lado)?",
            "O que foi apreendido e onde estava?",
            "Antecedentes, residência fixa, trabalho, filhos ou dependentes sob seus cuidados.",
            "Idade do cliente na data do fato.",
            "Quem pode depor a favor? Há câmeras no local?",
        ],
        documentos=[
            "Auto de prisão em flagrante, boletim de ocorrência, cópia integral do inquérito ou da ação penal.",
            "Denúncia ou queixa, decisões sobre a prisão, laudos periciais.",
            "Certidão de antecedentes; comprovantes de residência e de trabalho.",
            "Imagens de câmeras, prontuários médicos, registros de ligações e mensagens.",
            "Perícia defensiva quando o laudo oficial for contestado.",
        ],
        acordo=[
            "Acordo de não persecução penal (CPP, art. 28-A): pena mínima inferior a 4 anos, sem violência ou "
            "grave ameaça, com confissão.",
            "Transação penal e suspensão condicional do processo (Lei 9.099/1995, arts. 76 e 89); composição civil "
            "dos danos (art. 74).",
            "Avalie com o advogado se o acordo é vantajoso diante das teses de absolvição.",
        ],
        minuta=[
            "Respeite os prazos curtos e o momento do rol de testemunhas (na resposta à acusação, sob pena de preclusão).",
            "Organize os pedidos do principal ao subsidiário: nulidade, absolvição, desclassificação, pena mínima, "
            "regime mais brando, substituição da pena.",
            "No habeas corpus e nos pedidos de liberdade, descreva o constrangimento ilegal de forma objetiva e "
            "peça a liminar quando houver urgência.",
        ],
        cautelas=[
            "Presunção de inocência: não trate o cliente como culpado nem conclua sobre os fatos antes da prova.",
            "Nunca oriente destruir ou ocultar provas, influenciar testemunhas ou fugir; foque na defesa técnica legítima.",
        ],
    ),
    # ------------------------------------------------------------------ Administrativo
    _area(
        "administrativo", "Direito Administrativo",
        "Servidores públicos, concursos, licitações, multas, processos administrativos e responsabilidade do Estado.",
        ["administrativo", "civel", "juizados", "superiores", "extrajudicial"],
        foco=[
            "Ente e órgão envolvidos (União, estado, município, autarquia, fundação, empresa pública) e a autoridade "
            "que praticou o ato.",
            "Validade do ato: competência, forma, motivo, finalidade e objeto; motivação (Lei 9.784/1999, art. 50); "
            "contraditório e ampla defesa (Constituição, art. 5º, LV); consequências práticas da decisão (LINDB, arts. 20 a 30).",
            "Servidor público: regime (estatutário — Lei 8.112/1990 no federal ou estatuto local —, celetista, "
            "temporário, comissionado), estabilidade, remuneração, processo administrativo disciplinar.",
            "Concurso público (Constituição, art. 37, II): vinculação ao edital, aprovação dentro das vagas, "
            "preterição, critérios de correção e de heteroidentificação.",
            "Licitações e contratos (Lei 14.133/2021): habilitação, julgamento, reequilíbrio econômico-financeiro, "
            "sanções e rescisão.",
            "Responsabilidade civil do Estado: objetiva por ação (Constituição, art. 37, § 6º), discussão de culpa na omissão.",
            "Improbidade administrativa (Lei 8.429/1992, alterada pela Lei 14.230/2021): exige dolo.",
            "Poder de polícia e multas (trânsito, vigilância sanitária, posturas), desapropriação "
            "(Decreto-Lei 3.365/1941), acesso à informação (Lei 12.527/2011), fornecimento de medicamentos pelo SUS.",
        ],
        tribunais=[
            "Justiça Federal para União e entes federais (Constituição, art. 109, I); Justiça Estadual (Vara da "
            "Fazenda Pública) para estados e municípios; Juizados Especiais Federais e da Fazenda Pública até 60 "
            "salários mínimos (Lei 12.153/2009).",
            "Tribunais de Contas na esfera de controle externo.",
            "Tribunais superiores: STJ e STF (muitos temas de servidor e de responsabilidade estatal são constitucionais).",
        ],
        prazos=[
            "Prescrição contra a Fazenda Pública: 5 anos (Decreto 20.910/1932).",
            "Mandado de segurança: 120 dias da ciência do ato (Lei 12.016/2009, art. 23).",
            "Recurso administrativo federal: 10 dias (Lei 9.784/1999, art. 59); decadência de 5 anos para a "
            "administração anular ato favorável (art. 54).",
            "Prescrição da punição disciplinar federal (Lei 8.112/1990, art. 142).",
        ],
        perguntas=[
            "Qual órgão e qual autoridade praticou o ato? Quando o cliente tomou ciência?",
            "Houve processo administrativo com defesa? A decisão foi fundamentada?",
            "Qual o vínculo do servidor (cargo, efetivo ou não, data de posse)?",
            "No concurso: edital, número de vagas, classificação e nomeações feitas.",
            "No contrato público: o que mudou nos custos e quando a administração foi avisada?",
            "Qual o dano sofrido e como ele se liga à conduta do poder público?",
        ],
        documentos=[
            "Ato impugnado e sua publicação no Diário Oficial; cópia integral do processo administrativo.",
            "Edital e resultados; contrato administrativo, aditivos e medições.",
            "Ficha funcional, contracheques, portarias.",
            "Protocolos, notificações e respostas do órgão.",
        ],
        acordo=[
            "Autocomposição com a administração (Lei 13.140/2015, arts. 32 e seguintes) e câmaras de conciliação "
            "da advocacia pública.",
            "Pedido de reconsideração ou recurso administrativo antes da via judicial, quando útil.",
        ],
        minuta=[
            "Mandado de segurança: indique a autoridade coatora e a pessoa jurídica a que pertence; só prova pré-constituída.",
            "Liminares contra o poder público têm restrições legais (Lei 8.437/1992; Lei 12.016/2009, art. 7º, § 2º): "
            "fundamente a urgência considerando-as.",
            "Considere as prerrogativas da Fazenda: prazo em dobro (CPC, art. 183), remessa necessária (art. 496), "
            "pagamento por precatório ou RPV (Constituição, art. 100).",
        ],
        cautelas=[
            "Benefício do INSS é área previdenciária; tributo é área tributária: aponte se o caso for desses.",
            "Não afirme ilegalidade do ato sem identificar qual requisito foi violado.",
        ],
    ),
    # ------------------------------------------------------------------ Imobiliário
    _area(
        "imobiliario", "Direito Imobiliário",
        "Compra e venda de imóveis, locação, posse, usucapião, condomínio, distrato e vícios de construção.",
        ["civel", "juizados", "superiores", "extrajudicial"],
        foco=[
            "Situação registral: quem consta na matrícula, ônus e averbações. Só se adquire a propriedade com o "
            "registro (Código Civil, art. 1.245); contrato de gaveta gera direitos, mas exige cautela.",
            "Compra e venda e promessa: inadimplemento, atraso na entrega de imóvel na planta (tolerância de 180 "
            "dias — Lei 4.591/1964, art. 43-A), distrato e retenção (Lei 13.786/2018). Com incorporadora, o CDC "
            "costuma se aplicar.",
            "Locação (Lei 8.245/1991): despejo por falta de pagamento (art. 62) com liminar (art. 59, § 1º), "
            "renovatória (art. 51), revisional (art. 19), garantias (art. 37), benfeitorias (arts. 35 e 36).",
            "Posse: ações possessórias (CPC, arts. 554 a 568), força nova ou velha (art. 558), usucapião "
            "(Código Civil, arts. 1.238 a 1.244; Constituição, arts. 183 e 191) judicial ou extrajudicial "
            "(Lei 6.015/1973, art. 216-A).",
            "Condomínio edilício (Código Civil, arts. 1.331 a 1.358): cotas como obrigação que acompanha o imóvel "
            "(art. 1.345), multas, convenção e assembleias.",
            "Vícios construtivos: garantia de solidez e segurança (Código Civil, art. 618) e vícios de consumo.",
            "Alienação fiduciária (Lei 9.514/1997): consolidação da propriedade e leilões; bem de família "
            "(Lei 8.009/1990) e suas exceções; regularização fundiária (Lei 13.465/2017); direito de vizinhança (art. 1.277).",
        ],
        tribunais=[
            "Justiça Estadual; ações reais imobiliárias no foro da situação do imóvel (CPC, art. 47).",
            "Tribunal superior de referência: STJ; STF só com questão constitucional genuína.",
        ],
        prazos=[
            "Renovatória: proposta entre 1 ano e 6 meses antes do fim do contrato, sob pena de decadência "
            "(Lei 8.245/1991, art. 51, § 5º).",
            "Revisional de aluguel após 3 anos de vigência ou do último acordo (art. 19).",
            "Vício de solidez: garantia de 5 anos e ação em 180 dias do aparecimento (Código Civil, art. 618, parágrafo único).",
            "Cotas condominiais prescrevem em 5 anos (Código Civil, art. 206, § 5º, I).",
            "Posse nova (menos de ano e dia) permite liminar possessória (CPC, art. 558).",
        ],
        perguntas=[
            "O imóvel está registrado em nome de quem? Há matrícula atualizada?",
            "Qual o contrato (escritura, promessa, contrato particular) e o que já foi pago?",
            "Na posse: desde quando, de que forma, alguém contestou, há benfeitorias?",
            "Em nome de quem estão IPTU e contas de consumo?",
            "Na locação: prazo, garantia, valor, meses em atraso, notificações feitas.",
            "No vício construtivo: quando apareceu, se foi comunicado à construtora, se há laudo.",
        ],
        documentos=[
            "Matrícula atualizada e certidão de ônus reais; escritura ou contrato.",
            "Recibos, comprovantes, carnês de IPTU, contas de consumo (prova de posse).",
            "Contrato de locação, laudo de vistoria, notificações.",
            "Convenção, regimento e atas do condomínio.",
            "Fotos, plantas, habite-se e laudo de engenharia; perícia quando o vício for discutido.",
        ],
        acordo=[
            "Acordo de desocupação ou de pagamento na locação; renegociação com a incorporadora.",
            "Mediação condominial e usucapião extrajudicial em cartório quando houver consenso.",
        ],
        minuta=[
            "Valor da causa conforme a ação (na locação, 12 meses de aluguel — Lei 8.245/1991, art. 58, III; "
            "nas ações sobre o imóvel, CPC, art. 292).",
            "Descreva o imóvel com matrícula, endereço e área, usando marcadores quando faltarem.",
            "Peça a liminar possessória ou de despejo só quando os requisitos estiverem no caso.",
        ],
        cautelas=[
            "Não afirme quem é o proprietário sem a matrícula.",
            "Imóvel comprado de incorporadora também é relação de consumo: combine as duas análises.",
        ],
    ),
    # ------------------------------------------------------------------ Ambiental
    _area(
        "ambiental", "Direito Ambiental",
        "Autos de infração ambientais, licenciamento, APP e reserva legal, dano ambiental e crimes ambientais.",
        ["administrativo", "civel", "penal", "superiores", "extrajudicial"],
        foco=[
            "Separe as três esferas, que são independentes (Constituição, art. 225, § 3º): administrativa, civil e penal.",
            "Civil: responsabilidade objetiva e solidária pela reparação (Lei 6.938/1981, art. 14, § 1º); a obrigação "
            "acompanha o imóvel, inclusive para quem o comprou já degradado.",
            "Administrativa: auto de infração, multa e embargo (Lei 9.605/1998 e Decreto 6.514/2008): competência do "
            "órgão autuante, descrição da conduta, dosimetria da multa, nulidades do auto.",
            "Penal: crimes ambientais (Lei 9.605/1998), inclusive da pessoa jurídica (art. 3º).",
            "Licenciamento: competência do ente (LC 140/2011), licenças, condicionantes, estudos ambientais; "
            "confira a Lei Geral do Licenciamento Ambiental (Lei 15.190/2025), sua vigência e os vetos.",
            "Código Florestal (Lei 12.651/2012): APP (art. 4º), reserva legal (art. 12), CAR (art. 29), PRA (art. 59), "
            "área rural consolidada até 22/07/2008 (art. 3º, IV).",
            "Unidades de conservação (Lei 9.985/2000), recursos hídricos e outorga (Lei 9.433/1997), resíduos sólidos "
            "(Lei 12.305/2010), poluição sonora e atmosférica.",
            "Ação civil pública (Lei 7.347/1985) e termo de ajustamento de conduta com o Ministério Público.",
        ],
        tribunais=[
            "Justiça Estadual em regra; Justiça Federal quando há interesse da União, de autarquia federal (IBAMA, "
            "ICMBio) ou bem federal (rio federal, terra indígena, mar territorial).",
            "Esfera administrativa: órgão ambiental federal, estadual ou municipal autuante.",
            "Tribunais superiores: STJ e STF (o meio ambiente é tema constitucional, art. 225).",
        ],
        prazos=[
            "Defesa contra auto de infração federal: 20 dias (Decreto 6.514/2008, art. 113); confira o prazo estadual "
            "ou municipal quando o órgão for outro.",
            "Prescrição da punição administrativa em 5 anos e intercorrente em 3 anos (Lei 9.873/1999; Decreto "
            "6.514/2008, art. 21).",
            "A reparação civil do dano ambiental é tratada pela jurisprudência como imprescritível: confira a fonte.",
        ],
        perguntas=[
            "Qual a atividade ou o imóvel e qual órgão autuou? Data da autuação e da ciência.",
            "Há licença ambiental? Está vigente? As condicionantes foram cumpridas?",
            "A área é APP ou reserva legal? O imóvel está no CAR?",
            "Quando ocorreu a intervenção? Antes ou depois de 22/07/2008?",
            "Houve dano efetivo? Existe laudo ou imagem que mostre a situação anterior?",
            "O cliente comprou o imóvel já com o problema?",
            "Há inquérito civil, termo de ajustamento proposto ou ação penal?",
        ],
        documentos=[
            "Auto de infração, termo de embargo, relatório de fiscalização.",
            "Licenças, outorgas, CAR, matrícula do imóvel.",
            "Imagens de satélite históricas, fotos datadas, laudos técnicos e relatórios de monitoramento.",
            "Perícia ambiental quando o dano ou a sua extensão forem discutidos.",
        ],
        acordo=[
            "Termo de ajustamento de conduta (Lei 7.347/1985, art. 5º, § 6º) e adesão ao PRA.",
            "Conversão da multa em serviços ambientais (Decreto 6.514/2008, arts. 139 e seguintes) e conciliação ambiental.",
        ],
        minuta=[
            "Trate cada esfera em seu próprio tópico; não misture defesa administrativa com responsabilidade civil.",
            "Peça perícia técnica e indique as imagens e laudos que comprovam a situação da área.",
            "Contra embargo que paralisa a atividade, avalie pedido de efeito suspensivo ou tutela de urgência.",
        ],
        cautelas=[
            "Absolvição penal ou nulidade do auto não afastam automaticamente a reparação civil.",
            "Não afirme que a área está ou não em APP sem dados técnicos (largura do rio, declividade, localização).",
        ],
    ),
    # ------------------------------------------------------------------ Digital
    _area(
        "digital", "Direito Digital",
        "Proteção de dados (LGPD), remoção de conteúdo, perfis falsos, golpes e crimes na internet.",
        ["civel", "juizados", "penal", "superiores", "extrajudicial"],
        foco=[
            "Proteção de dados (LGPD, Lei 13.709/2018): base legal do tratamento (art. 7º; dados sensíveis, art. 11), "
            "direitos do titular (art. 18), incidente de segurança e comunicação (art. 48), responsabilidade "
            "(arts. 42 a 45), atuação da ANPD.",
            "Marco Civil da Internet (Lei 12.965/2014): remoção de conteúdo, responsabilidade do provedor (arts. 19 e 21), "
            "guarda de registros (arts. 13 e 15) e fornecimento de dados para identificar autor (art. 22). O STF revisou "
            "em 2025 o regime do art. 19: confira o entendimento vigente antes de dizer que só ordem judicial "
            "responsabiliza a plataforma.",
            "Perfis falsos, contas invadidas, ofensas e exposição: identificação do autor, remoção e indenização.",
            "Divulgação de cena íntima sem consentimento (CP, art. 218-C; Marco Civil, art. 21).",
            "Golpes e fraudes: fraude eletrônica (CP, art. 171, § 2º-A), responsabilidade de bancos e instituições de "
            "pagamento por falhas de segurança, Mecanismo Especial de Devolução (MED) do Pix.",
            "Crimes cibernéticos: invasão de dispositivo (CP, art. 154-A), perseguição (art. 147-A), intimidação "
            "sistemática virtual (art. 146-A), crimes contra a honra na internet.",
            "Comércio eletrônico (Decreto 7.962/2013), contratos e assinaturas eletrônicas (MP 2.200-2/2001; "
            "Lei 14.063/2020), software e direitos autorais (Leis 9.609/1998 e 9.610/1998).",
            "Crianças e adolescentes em ambiente digital: confira as normas recentes de proteção (ECA Digital, 2025) e sua vigência.",
        ],
        tribunais=[
            "Justiça Estadual em regra (Juizado Especial Cível ou Vara Cível); Justiça Federal em hipóteses específicas, "
            "como crimes transnacionais previstos em tratado.",
            "Esfera administrativa: ANPD (dados pessoais), Procon (consumo).",
            "Tribunais superiores: STJ e STF (liberdade de expressão e privacidade são temas constitucionais).",
        ],
        prazos=[
            "Guarda obrigatória de registros é curta (1 ano para conexão e 6 meses para aplicações — Marco Civil, "
            "arts. 13 e 15): peça a preservação com urgência.",
            "Reparação civil em 3 anos (Código Civil, art. 206, § 3º, V) ou 5 anos se houver relação de consumo (CDC, art. 27).",
            "Representação ou queixa nos crimes contra a honra e outros dependentes da vítima: 6 meses do conhecimento "
            "da autoria (CP, art. 103).",
            "No Pix, a contestação pelo MED tem prazo curto junto ao banco: verifique se foi feita.",
        ],
        perguntas=[
            "Qual plataforma, quais URLs ou perfis, e desde quando o conteúdo está no ar?",
            "O cliente já denunciou na plataforma? Há protocolo ou resposta?",
            "Quem viu, compartilhou ou comentou? Qual o alcance?",
            "Nos golpes: data, valor, banco, chave Pix de destino; contestou no banco e registrou boletim de ocorrência?",
            "No vazamento: quais dados, como soube, a empresa comunicou o incidente, já houve uso indevido?",
            "O autor é conhecido ou anônimo?",
        ],
        documentos=[
            "Prints com URL, data e hora; ata notarial (CPC, art. 384) ou captura técnica com registro de integridade.",
            "Links dos conteúdos e perfis, identificadores de usuário.",
            "Comprovantes de transações, extratos, protocolos de contestação no banco.",
            "Boletim de ocorrência; e-mails de comunicação de incidente; respostas da empresa.",
            "Perícia em dispositivo ou em conta quando a autoria ou a invasão forem discutidas.",
        ],
        acordo=[
            "Notificação à plataforma e requerimento ao controlador de dados (LGPD, art. 18).",
            "Reclamação à ANPD ou ao Procon; acordo de remoção, retratação ou indenização.",
        ],
        minuta=[
            "Tutela de urgência para remover conteúdo e preservar e fornecer registros, com a identificação clara e "
            "específica de cada URL (Marco Civil, art. 19, § 1º) e os requisitos do art. 22 (indícios, justificativa, período).",
            "Inclua a plataforma como ré ou requerida quando for preciso obter dados do autor anônimo.",
            "Liste as provas digitais com data de captura e forma de preservação.",
        ],
        cautelas=[
            "Prova digital some rápido: priorize preservação antes de qualquer outra providência.",
            "Equilibre a remoção com a liberdade de expressão: crítica legítima não é ilícito.",
        ],
    ),
]

_POR_ID = {a["id"]: a for a in AREAS}
AREAS_JURIDICAS = frozenset(_POR_ID)


def normalizar_area(valor: Any) -> Optional[str]:
    """Id da área no catálogo, aceitando alguns apelidos ("criminal" -> "penal"). None se não houver."""
    chave = str(valor or "").strip().lower()
    chave = _ALIASES.get(chave, chave)
    return chave if chave in _POR_ID else None


def obter_area(valor: Any) -> Optional[Dict[str, Any]]:
    area_id = normalizar_area(valor)
    return _POR_ID[area_id] if area_id else None


def orientacao_da_area(valor: Any, tarefa: str) -> str:
    """Bloco de texto que vai depois do SYSTEM_PROMPT. Vazio quando a área não é conhecida."""
    if tarefa not in _BLOCOS_POR_TAREFA:
        raise ValueError(f"Tarefa inválida: {tarefa}")
    area = obter_area(valor)
    if not area:
        return ""
    partes = [_CABECALHO.format(nome=area["nome"].upper())]
    for bloco in _BLOCOS_POR_TAREFA[tarefa]:
        itens = "\n".join(f"- {item}" for item in area[bloco])
        partes.append(f"{_TITULOS[bloco]}:\n{itens}")
    if tarefa == "analise":
        partes.append(_FECHO_ANALISE)
    return "\n\n".join(partes)


def area_front(area: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": area["id"], "nome": area["nome"], "descricao": area["descricao"],
            "gruposPecas": list(area["grupos_pecas"])}
