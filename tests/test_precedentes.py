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
from analise.catalogo import previdenciario  # noqa: E402
from analise.catalogo.base import stj  # noqa: E402
from analise.llm_providers import BaseLLMProvider  # noqa: E402

DOMINIOS_OFICIAIS = ("https://portal.stf.jus.br/", "https://noticias.stf.jus.br/", "https://www.stf.jus.br/",
                     "https://processo.stj.jus.br/", "https://scon.stj.jus.br/", "https://www.cjf.jus.br/",
                     "https://www.trf4.jus.br/", "https://portal.trt3.jus.br/", "https://www.trt4.jus.br/",
                     "https://ejud.tjpr.jus.br/")

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


class TodasAsAreas(unittest.TestCase):
    def test_as_12_areas_tem_catalogo(self):
        self.assertEqual(set(precedentes.CATALOGO), set(areas.AREAS_JURIDICAS))

    def test_ids_de_sub_area_sao_unicos_por_area(self):
        for area_id, subs in precedentes.CATALOGO.items():
            ids = [s["id"] for s in subs]
            self.assertEqual(len(ids), len(set(ids)), area_id)

    def test_cada_area_acha_um_caso_tipico(self):
        casos = {
            "civil": "Bloquearam minha poupança na execução da dívida",
            "familia-sucessoes": "O pai não paga a pensão alimentícia e quero a prisão civil",
            "trabalhista": "Fazia horas extras sem receber e não tinha intervalo de almoço",
            "penal": "Fui preso em flagrante com maconha para uso próprio",
            "tributario": "Tenho câncer e sou aposentado, quero isenção do imposto de renda",
            "administrativo": "Passei no concurso dentro das vagas e não fui nomeado",
            "imobiliario": "A construtora atrasou a entrega das chaves do apartamento na planta",
            "ambiental": "A empresa causou poluição no rio e perdi a pesca",
            "digital": "Publicaram ofensas no Instagram e a plataforma não removeu",
            "empresarial": "A devedora entrou em recuperação judicial e o sócio era avalista",
        }
        for area_id, texto in casos.items():
            bloco = precedentes.bloco_precedentes(area_id, "analise", texto)
            self.assertIn("SUB-ÁREA:", bloco, area_id)
            self.assertIn("16/11/2026", bloco, area_id)


class Selecao(unittest.TestCase):
    def test_caso_de_epi_traz_tempo_especial_e_nao_bpc(self):
        texto = "Trabalhei 20 anos em metalúrgica; o PPP diz que o EPI era eficaz, mas o ruído era alto."
        bloco = precedentes.bloco_precedentes("previdenciario", "analise", texto)
        self.assertIn("STJ, Tema 1090", bloco)
        self.assertIn("STF, Tema 555", bloco)
        self.assertNotIn("BPC/LOAS", bloco)
        self.assertIn(previdenciario.VERIFICADO, bloco)

    def test_acentos_e_maiusculas_nao_atrapalham(self):
        bloco = precedentes.bloco_precedentes("consumidor", "analise", "O VOO ATRASOU e a BAGAGEM sumiu")
        self.assertIn("Tema 1240", bloco)

    def test_sem_texto_ou_sem_catalogo_nada_entra(self):
        self.assertEqual(precedentes.bloco_precedentes("previdenciario", "analise", ""), "")
        self.assertEqual(precedentes.bloco_precedentes("inexistente", "analise", "horas extras e EPI"), "")
        self.assertEqual(precedentes.bloco_precedentes("consumidor", "analise", "contrato de compra e venda"), "")

    def test_no_maximo_tres_sub_areas_e_cabe_no_limite(self):
        for area_id, texto in TUDO.items():
            escolhidas = precedentes.subareas_relevantes(area_id, texto)
            esperado = min(precedentes.LIMITE_SUBAREAS, len(precedentes.CATALOGO[area_id]))
            self.assertEqual(len(escolhidas), esperado, area_id)
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


class ColunaDePrecedentes(unittest.TestCase):
    def _front(self, dados):
        base = {"resumo_caso": "r", "teses": [], "temas_stf_stj": [], "jurisprudencia": [],
                "perguntas_sugeridas": [], "necessidades_adicionais": []}
        base.update(dados)
        from analise import mapeador
        return mapeador.para_analise_front({"versao": 1, "gerada_em": "d", "analise": base}, "c")["insights"]

    def test_tema_chega_com_nivel_tribunal_e_situacao(self):
        itens = self._front({"temas_stf_stj": [
            {"titulo": "Prova nova", "descricao": "d", "relevancia": "alta", "tribunal": "STJ",
             "identificador": "Tema 1124", "especie": "repetitivo", "nivel": "N1", "situacao": "em_atencao",
             "fonte": "STJ, Tema 1124 https://processo.stj.jus.br/x"}]})
        i = itens[0]
        self.assertEqual((i["categoria"], i["nivel"], i["tribunal"], i["identificador"], i["situacao"]),
                         ("tema_superior", "N1", "STJ", "Tema 1124", "em_atencao"))

    def test_nivel_deduzido_quando_a_ia_nao_informa(self):
        itens = self._front({"temas_stf_stj": [
            {"titulo": "Súmula 47 da TNU", "descricao": "d", "relevancia": "media", "fonte": "TNU, Súmula 47"},
            {"titulo": "Súmula 9 da TRU4", "descricao": "d", "relevancia": "media", "fonte": "TRU4, Súmula 9"},
            {"titulo": "Tema 709 do STF", "descricao": "d", "relevancia": "media", "fonte": "STF, Tema 709"}]})
        self.assertEqual([i["nivel"] for i in itens], ["N2", "N3", "N1"])

    def test_sumula_posta_em_jurisprudencia_vai_para_precedentes(self):
        # Caso real: a IA pôs "Súmula 75 da TNU" em jurisprudência.
        itens = self._front({"jurisprudencia": [
            {"titulo": "Presunção relativa da CTPS", "tribunal": "TNU", "processo": "Súmula 75", "data": None,
             "resumo": "r", "status": "majoritaria", "fonte": "TNU, Súmula 75 https://www.cjf.jus.br/x"},
            {"titulo": "Trabalho rural antes dos 12 anos", "tribunal": "STJ", "processo": "AgInt no AREsp 956.558/SP",
             "data": None, "resumo": "r", "status": "em_analise", "fonte": "STJ https://processo.stj.jus.br/y"}]})
        self.assertEqual([i["categoria"] for i in itens], ["tema_superior", "jurisprudencia"])
        self.assertEqual((itens[0]["nivel"], itens[0]["identificador"]), ("N2", "Súmula 75"))

    def test_prompt_manda_precedentes_para_a_coluna_certa(self):
        self.assertIn("PRECEDENTES QUALIFICADOS", analysis.SYSTEM_PROMPT)
        self.assertIn('"nivel": "N1|N2|N3"', analysis.SYSTEM_PROMPT)
        bloco = precedentes.bloco_precedentes("previdenciario", "analise", "PPP com EPI eficaz")
        self.assertIn('nunca em "jurisprudencia"', bloco)
        self.assertNotIn("em_analise", bloco)


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
        url = stj(1090)
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
