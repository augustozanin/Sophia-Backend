"""Direito Digital: precedentes curados (conferidos em 16/11/2026: STF — página do tema e tese oficial —, STJ —
temas)."""
from .base import p, stf, stj, sub

ALCANCE = "regional do TJ indicado (RS, SC ou PR), só para casos que tramitam lá"

SUBAREAS = [
    sub("conteudo-plataformas", "Conteúdo ofensivo, remoção e responsabilidade de plataformas",
        [r"rede social", r"instagram", r"facebook", r"tiktok", r"youtube", r"\bx\b|twitter", r"whatsapp",
         r"postag", r"publicac", r"perfil falso", r"conta falsa", r"remover", r"remocao", r"ofens", r"difama",
         r"exposic", r"nudes|intimas", r"marco civil", r"provedor", r"plataforma"],
        [
            p("STF, Tema 987 (RE 1.037.396)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 17/06/2026",
              "Marco Civil, art. 19: plataforma responde após notificação em ilícitos",
              "Publicaram conteúdo ilícito sobre o cliente e a plataforma não removeu após o aviso.",
              "O art. 19 é parcialmente inconstitucional. Em crimes e atos ilícitos (e contas inautênticas), a "
              "plataforma responde se não remover após notificação extrajudicial (art. 21). Crimes contra a honra "
              "seguem o art. 19 (ordem judicial), mas réplicas de ofensa já reconhecida em juízo devem ser removidas "
              "por notificação. Anúncios pagos e robôs têm responsabilidade presumida.",
              '"Tema 987" STF "art. 19" Marco Civil notificação', stf(987),
              "Há ainda dever de remoção imediata de crimes graves de rol taxativo, por falha sistêmica. Notifique a "
              "plataforma por escrito e guarde o protocolo antes de ajuizar."),
            p("STF, Tema 533 (RE 1.057.258)", "N1", "tese de repercussão geral, nacional", "EM ATENÇÃO",
              "acórdão de mérito publicado em 05/11/2025, sem trânsito em julgado; mesma tese do Tema 987",
              "Hospedagem de conteúdo: mesma regra do Tema 987",
              "O conteúdo ofensivo está num site ou serviço que hospeda publicações de terceiros.",
              "O STF fixou para o Tema 533 a mesma tese do Tema 987, sobre a inconstitucionalidade parcial do art. 19 "
              "do Marco Civil.",
              '"Tema 533" STF hospedagem conteúdo "art. 19"', stf(533)),
            p("STF, Tema 786 (RE 1.010.606)", "N1", "tese de repercussão geral, nacional", "VIGENTE",
              "trânsito em julgado em 28/05/2021",
              "Não existe direito ao esquecimento",
              "O cliente quer apagar notícias verdadeiras e antigas sobre ele.",
              "É incompatível com a Constituição um direito ao esquecimento que impeça, pela passagem do tempo, a "
              "divulgação de fatos verídicos licitamente obtidos; abusos se analisam caso a caso (honra, imagem, "
              "privacidade).",
              '"Tema 786" STF direito ao esquecimento', stf(786),
              "Desfavorável: fundamente em abuso concreto (dados falsos, exposição desnecessária), não no tempo."),
        ], lacunas="N2 e N3: sem precedente verificado."),
    sub("golpes-digitais", "Golpes e fraudes digitais",
        [r"golpe", r"\bpix\b", r"hacke", r"invadi\w* (a )?conta", r"clonad", r"phishing", r"boleto falso",
         r"perfil clonado", r"vazamento de dados", r"\blgpd\b", r"dados pessoais"],
        [
            p("STJ, Tema 466", "N1", "tese repetitiva, nacional (originou a Súmula 479/STJ)", "VIGENTE",
              "trânsito em julgado",
              "Fraude em operação bancária é risco do banco",
              "O cliente caiu num golpe digital que passou pelo banco (Pix, conta aberta em seu nome).",
              "Instituições financeiras respondem objetivamente pelos danos de fortuito interno ligados a fraudes e "
              "delitos de terceiros em operações bancárias.",
              '"Tema 466" STJ fortuito interno fraude banco', stj(466),
              "Em engenharia social pura, o STJ decide caso a caso; vazamento de dados e LGPD não têm tese "
              "vinculante verificada."),
        ], lacunas="N2 e N3: sem precedente verificado. Vazamento de dados (LGPD): sem tese vinculante verificada."),
]
