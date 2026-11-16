"""Catálogo curado de precedentes (analise/precedentes.py) e sua entrada nos prompts.
Rodar na raiz do backend:  python -m unittest discover -s tests -v
"""
import json
import os
import sys
import unittest
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analise import analysis, areas, precedentes  # noqa: E402
from analise.llm_providers import BaseLLMProvider  # noqa: E402

DOMINIOS_OFICIAIS = ("https://portal.stf.jus.br/", "https://noticias.stf.jus.br/", "https://www.stf.jus.br/",
                     "https://processo.stj.jus.br/", "https://scon.stj.jus.br/", "https://www.cjf.jus.br/",
                     "https://www.trf4.jus.br/")

# Um caso que toca todas as sub-áreas de cada área: o pior caso de tamanho do prompt.
TUDO = {
    area_id: " ".join(p.replace("\\b", "").replace("\\w*", "").replace("[- ]", " ").replace("?", "")
                      for sub in subs for p in sub["palavras"])
    for area_id, subs in precedentes.CATALOGO.items()
}


class Falso(BaseLLMProvider):
    name, env_var, fallback_model = "falso", "X", "m"

    def __init__(self, saidas):
        super().__init__("k")
        self.saidas, self.sistemas = list(saidas), []

    def generate(self, system_prompt, user_prompt, use_web_search=True, json_mode=False):
        self.sistemas.append(system_prompt)
        return self.saidas.pop(0)


class Catalogo(unittest.TestCase):
    def test_todo_precedente_tem_os_campos_e_fonte_oficial(self):
        for area_id, subs in precedentes.CATALOGO.items():
            self.assertIn(area_id, areas.AREAS_JURIDICAS)
            for sub in subs:
                self.assertTrue(sub["nome"] and sub["palavras"], sub["id"])
                for p in sub["precedentes"]:
                    contexto = (area_id, sub["id"], p["id"])
                    self.assertIn(p["status"], precedentes.STATUS, contexto)
                    self.assertIn(p["nivel"], precedentes.NIVEIS, contexto)
                    for campo in ("id", "especie", "motivo", "titulo", "fato", "tese", "busca", "fonte"):
                        self.assertTrue(p[campo].strip(), (contexto, campo))
                    self.assertTrue(p["fonte"].startswith(DOMINIOS_OFICIAIS), contexto)

    def test_respeita_o_teto_por_nivel(self):
        # Briefing: até 3 N1, 2 N2 e 1 N3 por sub-área.
        teto = {"N1": 3, "N2": 2, "N3": 1}
        for subs in precedentes.CATALOGO.values():
            for sub in subs:
                contagem = Counter(p["nivel"] for p in sub["precedentes"])
                for nivel, maximo in teto.items():
                    self.assertLessEqual(contagem[nivel], maximo, (sub["id"], nivel))

    def test_superado_e_nao_verificado_vem_com_alerta(self):
        for subs in precedentes.CATALOGO.values():
            for sub in subs:
                for p in sub["precedentes"]:
                    if p["status"] in ("SUPERADO", "NÃO VERIFICADO", "EM ATENÇÃO"):
                        self.assertTrue(p["motivo"].strip(), p["id"])
                    if p["status"] in ("SUPERADO", "NÃO VERIFICADO"):
                        self.assertTrue(p["alerta"].strip(), p["id"])

    def test_revisao_da_vida_toda_esta_marcada_como_superada(self):
        revisoes = next(s for s in precedentes.CATALOGO["previdenciario"] if s["id"] == "revisoes")
        vida_toda = next(p for p in revisoes["precedentes"] if "1102" in p["id"])
        self.assertEqual(vida_toda["status"], "SUPERADO")


class Selecao(unittest.TestCase):
    def test_caso_de_epi_traz_tempo_especial_e_nao_bpc(self):
        texto = "Trabalhei 20 anos em metalúrgica; o PPP diz que o EPI era eficaz, mas o ruído era alto."
        bloco = precedentes.bloco_precedentes("previdenciario", "analise", texto)
        self.assertIn("STJ, Tema 1090", bloco)
        self.assertIn("STF, Tema 555", bloco)
        self.assertNotIn("BPC/LOAS", bloco)
        self.assertIn(precedentes.VERIFICADO_EM, bloco)

    def test_acentos_e_maiusculas_nao_atrapalham(self):
        bloco = precedentes.bloco_precedentes("consumidor", "analise", "O VOO ATRASOU e a BAGAGEM sumiu")
        self.assertIn("Tema 1240", bloco)

    def test_sem_texto_ou_sem_catalogo_nada_entra(self):
        self.assertEqual(precedentes.bloco_precedentes("previdenciario", "analise", ""), "")
        self.assertEqual(precedentes.bloco_precedentes("trabalhista", "analise", "horas extras e EPI"), "")
        self.assertEqual(precedentes.bloco_precedentes("consumidor", "analise", "contrato de compra e venda"), "")

    def test_no_maximo_tres_sub_areas_e_cabe_no_limite(self):
        for area_id, texto in TUDO.items():
            escolhidas = precedentes.subareas_relevantes(area_id, texto)
            self.assertEqual(len(escolhidas), precedentes.LIMITE_SUBAREAS, area_id)
            for tarefa in areas.TAREFAS:
                bloco = precedentes.bloco_precedentes(area_id, tarefa, texto)
                # ~4 caracteres por token: no pior caso, ~2.300 tokens de precedentes.
                self.assertLessEqual(len(bloco), precedentes.ORCAMENTO[tarefa], (area_id, tarefa))
                self.assertIn("SUB-ÁREA:", bloco)

    def test_a_maior_sub_area_sozinha_cabe_no_orcamento(self):
        # A primeira sub-área entra mesmo acima do orçamento; nenhuma deve passar dele sozinha.
        for area_id, subs in precedentes.CATALOGO.items():
            for sub in subs:
                texto = " ".join(p.replace("\\b", "") for p in sub["palavras"][:1])
                for tarefa in areas.TAREFAS:
                    bloco = precedentes.bloco_precedentes(area_id, tarefa, texto)
                    self.assertLessEqual(len(bloco), precedentes.ORCAMENTO[tarefa], (sub["id"], tarefa))

    def test_chat_e_minuta_saem_mais_curtos(self):
        texto = "plano de saúde negou cirurgia fora do rol da ANS"
        analise = precedentes.bloco_precedentes("consumidor", "analise", texto)
        chat = precedentes.bloco_precedentes("consumidor", "chat", texto)
        minuta = precedentes.bloco_precedentes("consumidor", "minuta", texto)
        self.assertIn("Fato-tipo:", analise)
        self.assertIn("Busca:", analise)
        for outro in (chat, minuta):
            self.assertNotIn("Fato-tipo:", outro)
            self.assertNotIn("Busca:", outro)
            self.assertLess(len(outro), len(analise))
        self.assertIn("nunca como fundamento", minuta)
        self.assertIn("NÃO LISTA FECHADA", analise)


class Prompt(unittest.TestCase):
    def test_orientacao_sem_texto_continua_igual_e_sem_numeros(self):
        texto = areas.orientacao_da_area("previdenciario", "analise")
        self.assertNotIn("PRECEDENTES CURADOS", texto)
        self.assertIsNone(analysis._SPECIFIC_NUMBER_RE.search(texto))

    def test_analise_usa_o_relato_para_escolher_os_precedentes(self):
        p = Falso([json.dumps({"resumo_caso": "r", "teses": [], "temas_stf_stj": [], "jurisprudencia": [],
                               "perguntas_sugeridas": [], "necessidades_adicionais": []})])
        analysis.run_case_analysis(p, "Meu pai faleceu e eu vivia em união estável com ele.", "",
                                   area="previdenciario")
        self.assertIn("SUB-ÁREA: PENSÃO POR MORTE E DEPENDENTES", p.sistemas[0])
        self.assertTrue(p.sistemas[0].startswith(analysis.SYSTEM_PROMPT.rstrip()))

    def test_link_do_catalogo_sobrevive_a_validacao_e_inventado_nao(self):
        url = precedentes._stj(1090)
        resposta = {"resumo_caso": "r", "perguntas_sugeridas": [], "necessidades_adicionais": [],
                    "temas_stf_stj": [], "jurisprudencia": [],
                    "teses": [{"titulo": "EPI", "descricao": "Tema 1090", "relevancia": "alta",
                               "fonte": f"STJ, Tema 1090 {url}"},
                              {"titulo": "X", "descricao": "y", "relevancia": "baixa",
                               "fonte": "https://www.stj.jus.br/inventado"}]}
        p = Falso([json.dumps(resposta)])
        dados = analysis.run_case_analysis(p, "PPP com EPI eficaz", "", use_web_search=False,
                                           area="previdenciario")
        self.assertIn(url, dados["teses"][0]["fonte"])
        self.assertEqual(dados["teses"][1]["fonte"], "não verificado")

    def test_busca_na_web_confirma_o_catalogo_e_amplia(self):
        from analise.busca_web import INSTRUCAO_LINKS
        self.assertIn("1) CONFIRMAR", INSTRUCAO_LINKS)
        self.assertIn("2) AMPLIAR", INSTRUCAO_LINKS)
        self.assertIn("não lista fechada", INSTRUCAO_LINKS)

    def test_minuta_escreve_como_advogado_do_cliente_sem_inventar(self):
        sistema = analysis.system_prompt("minuta", "consumidor", "negativação indevida")
        self.assertIn("ADVOGADO DA PARTE CLIENTE", sistema)
        self.assertIn("subsidiárias", sistema)
        self.assertIn("LIMITES INEGOCIÁVEIS", sistema)
        self.assertIn("Nunca invente fato", sistema)
        # A minuta continua sem o JSON da análise e com o schema próprio no fim.
        self.assertTrue(sistema.rstrip().endswith(analysis.DRAFT_SYSTEM_SUFFIX.rstrip()))

    def test_chat_e_minuta_tambem_recebem(self):
        sistema, _ = analysis._prompts_do_chat({"resumo": "voo cancelado"}, [], "cabe dano moral?", "",
                                               "consumidor")
        self.assertIn("SUB-ÁREA: TRANSPORTE AÉREO", sistema)
        self.assertIn("Ao responder, diga a situação", sistema)


if __name__ == "__main__":
    unittest.main()
