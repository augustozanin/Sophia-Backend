"""Testes do módulo `prazos` sem rede e sem MongoDB de verdade.
Rodar em backend/:  python -m unittest discover -s tests -v
"""
import asyncio
import os
import sys
import unittest
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bson import ObjectId  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from prazos import djen, numeros, router  # noqa: E402
from prazos.storage import ArmazenamentoPrazos  # noqa: E402

ANA, BRUNO = "ana", "bruno"
PROCESSO = "10036864920158260586"  # 1003686-49.2015.8.26.0586, número real com DV válido
OUTRO_PROCESSO = "40977562720268260002"

HTML = (
    "<html><head><style>x{}</style></head><body><article>"
    "<section><b>USUCAPI&Atilde;O  N&ordm; 1003686-49.2015.8.26.0586/SP</b></section>"
    "<section><table><tr><td>AUTOR</td><td>: ANA</td></tr></table></section>"
    "<p>Vistos.</p><p><span>Evento 616: defiro.&nbsp;<u>Expe&ccedil;a-se nova carta.</u></span></p>"
    "</article></body></html>"
)


def item_djen(djen_id, processo=PROCESSO, data="2026-11-13", **extra):
    return {
        "id": djen_id, "data_disponibilizacao": data, "siglaTribunal": "TJSP", "tipoComunicacao": "Intimação",
        "nomeOrgao": "2ª Vara Cível", "texto": HTML, "numero_processo": processo, "link": "https://eproc/x",
        "tipoDocumento": "DESPACHO/DECISÃO", "nomeClasse": "USUCAPIÃO", "ativo": True,
        "destinatarios": [{"nome": "ANA", "polo": "A"}],
        "destinatarioadvogados": [{"advogado": {"nome": "RENATO", "numero_oab": "100000", "uf_oab": "SP"}}],
        **extra,
    }


# ---------------------------------------------------------------- Mongo falso (motor)
def _valor_bate(atual, esperado):
    if isinstance(esperado, dict):
        for op, alvo in esperado.items():
            if op == "$in" and not (atual in alvo or (isinstance(atual, list) and any(a in alvo for a in atual))):
                return False
            if op == "$gte" and not (atual is not None and atual >= alvo):
                return False
            if op == "$ne" and atual == alvo:
                return False
            if op == "$size" and not (isinstance(atual, list) and len(atual) == alvo):
                return False
        return True
    if isinstance(atual, list) and not isinstance(esperado, list):
        return esperado in atual
    return atual == esperado


def _bate(doc, filtro):
    for chave, esperado in filtro.items():
        if chave == "$or":
            if not any(_bate(doc, sub) for sub in esperado):
                return False
        elif not _valor_bate(doc.get(chave), esperado):
            return False
    return True


class _Resultado:
    def __init__(self, matched=0, upserted_id=None):
        self.matched_count, self.upserted_id = matched, upserted_id


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, chave, direcao=None):
        ordem = chave if isinstance(chave, list) else [(chave, direcao)]
        for campo, sentido in reversed(ordem):
            self.docs.sort(key=lambda d: (d.get(campo) is None, d.get(campo) or 0), reverse=sentido == -1)
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    async def to_list(self, length=None):
        return self.docs[:length] if length else self.docs


class _Colecao:
    def __init__(self):
        self.docs = []

    async def create_index(self, *a, **k):
        return "ok"

    async def insert_one(self, doc):
        doc.setdefault("_id", ObjectId())
        self.docs.append(dict(doc))

    def find(self, filtro):
        return _Cursor([dict(d) for d in self.docs if _bate(d, filtro)])

    async def find_one(self, filtro, sort=None):
        achados = [d for d in self.docs if _bate(d, filtro)]
        return dict(achados[0]) if achados else None

    @staticmethod
    def _aplicar(doc, mudanca, inserindo):
        doc.update(mudanca.get("$set", {}))
        if inserindo:
            doc.update(mudanca.get("$setOnInsert", {}))
        for campo, valor in mudanca.get("$addToSet", {}).items():
            lista = doc.setdefault(campo, [])
            if valor not in lista:
                lista.append(valor)
        for campo, valor in mudanca.get("$pull", {}).items():
            doc[campo] = [v for v in doc.get(campo, []) if v != valor]

    async def update_one(self, filtro, mudanca, upsert=False):
        for doc in self.docs:
            if _bate(doc, filtro):
                self._aplicar(doc, mudanca, False)
                return _Resultado(1)
        if not upsert:
            return _Resultado(0)
        novo = {k: v for k, v in filtro.items() if not k.startswith("$") and not isinstance(v, dict)}
        novo["_id"] = ObjectId()
        self._aplicar(novo, mudanca, True)
        self.docs.append(novo)
        return _Resultado(0, novo["_id"])

    async def update_many(self, filtro, mudanca):
        for doc in self.docs:
            if _bate(doc, filtro):
                self._aplicar(doc, mudanca, False)

    async def delete_one(self, filtro):
        for doc in self.docs:
            if _bate(doc, filtro):
                self.docs.remove(doc)
                return

    async def delete_many(self, filtro):
        self.docs = [d for d in self.docs if not _bate(d, filtro)]


class _Banco(dict):
    def __getitem__(self, nome):
        return self.setdefault(nome, _Colecao())


class DjenFalso:
    """Responde o que estiver em `itens`, filtrando por OAB ou processo como a API real."""

    def __init__(self, itens=None):
        self.itens, self.chamadas, self.status = list(itens or []), [], 200

    async def __call__(self, parametros):
        self.chamadas.append(dict(parametros))
        if self.status != 200:
            return self.status, None
        lote = [i for i in self.itens
                if ("numeroProcesso" not in parametros or i["numero_processo"] == parametros["numeroProcesso"])]
        inicio = (parametros["pagina"] - 1) * parametros["itensPorPagina"]
        return 200, {"status": "success", "count": len(lote),
                     "items": lote[inicio:inicio + parametros["itensPorPagina"]]}


def montar(itens=None, casos=None):
    banco = _Banco()
    arm = ArmazenamentoPrazos(banco)
    fonte = DjenFalso(itens)
    casos = casos or {(ANA, "caso-ana")}

    async def caso_do_usuario(user_id, caso_id):
        return (user_id, caso_id) in casos

    app = FastAPI()
    app.include_router(router.criar_router(lambda: arm, caso_do_usuario, fonte))
    return TestClient(app), banco, fonte


# ---------------------------------------------------------------- números
class Numeros(unittest.TestCase):
    def test_processo_real_tem_dv_valido(self):
        self.assertEqual(numeros.normalizar_processo("1003686-49.2015.8.26.0586"), (PROCESSO, None))
        self.assertEqual(numeros.formatar_processo(PROCESSO), "1003686-49.2015.8.26.0586")

    def test_digito_trocado_e_rejeitado(self):
        numero, erro = numeros.normalizar_processo("1003686-48.2015.8.26.0586")
        self.assertIsNone(numero)
        self.assertIn("dígito verificador", erro)

    def test_processo_curto_e_rejeitado(self):
        self.assertIsNotNone(numeros.normalizar_processo("123")[1])

    def test_oab_tira_mascara_e_zeros(self):
        self.assertEqual(numeros.normalizar_oab("0100.000", "sp"), ("100000", "SP", None))
        self.assertIsNotNone(numeros.normalizar_oab("100000", "XX")[2])
        self.assertIsNotNone(numeros.normalizar_oab("", "SP")[2])


# ---------------------------------------------------------------- DJEN
class Djen(unittest.TestCase):
    def test_texto_sai_sem_html_e_com_acentos(self):
        texto = djen.texto_puro(HTML)
        self.assertIn("USUCAPIÃO Nº 1003686-49.2015.8.26.0586/SP", texto)
        self.assertIn("Expeça-se nova carta.", texto)
        self.assertNotIn("<", texto)
        self.assertNotIn("x{}", texto)

    def test_normalizar_pega_os_campos_e_descarta_link_inseguro(self):
        n = djen.normalizar(item_djen(7, link="javascript:alert(1)"))
        self.assertEqual(n["djen_id"], 7)
        self.assertEqual(n["numero_processo"], PROCESSO)
        self.assertEqual(n["advogados"], [{"nome": "RENATO", "oab": "100000", "uf": "SP"}])
        self.assertIsNone(n["link"])
        self.assertFalse(n["cancelada"])

    def test_data_no_formato_brasileiro_tambem_vale(self):
        item = item_djen(8, data="")
        item["datadisponibilizacao"] = "13/11/2026"
        self.assertEqual(djen.normalizar(item)["data_disponibilizacao"], "2026-11-13")
        self.assertIsNone(djen.normalizar({"id": 9}))

    def test_paginacao_ate_acabar(self):
        fonte = DjenFalso([item_djen(i) for i in range(250)])
        itens = asyncio.run(djen.buscar_comunicacoes(fonte, {"numeroOab": "1", "ufOab": "SP"}, 10))
        self.assertEqual(len(itens), 250)
        self.assertEqual([c["pagina"] for c in fonte.chamadas], [1, 2, 3])

    def test_429_vira_erro_de_limite(self):
        fonte = DjenFalso()
        fonte.status = 429
        with self.assertRaises(djen.ErroDjen) as ctx:
            asyncio.run(djen.buscar_comunicacoes(fonte, {}, 3))
        self.assertTrue(ctx.exception.limite)


# ---------------------------------------------------------------- rotas
class Rotas(unittest.TestCase):
    def test_oab_nova_consulta_os_ultimos_30_dias_e_traz_as_intimacoes(self):
        cliente, _banco, fonte = montar([item_djen(1), item_djen(2, OUTRO_PROCESSO)])
        r = cliente.post("/prazos/monitoramentos",
                         json={"user_id": ANA, "tipo": "oab", "oab_numero": "100.000", "oab_uf": "sp"})
        self.assertEqual(r.status_code, 200, r.text)
        painel = r.json()["painel"]
        self.assertEqual(painel["monitoramentos"][0]["oabNumero"], "100000")
        self.assertEqual({p["situacao"] for p in painel["publicacoes"]}, {"pendente"})
        self.assertEqual(len(painel["publicacoes"]), 2)
        chamada = fonte.chamadas[0]
        self.assertEqual((chamada["numeroOab"], chamada["ufOab"]), ("100000", "SP"))
        hoje = router.agora().date()
        self.assertEqual(chamada["dataDisponibilizacaoInicio"], (hoje - timedelta(days=30)).isoformat())

    def test_processo_novo_busca_o_historico_inteiro(self):
        cliente, _banco, fonte = montar([item_djen(1)])
        r = cliente.post("/prazos/monitoramentos",
                         json={"user_id": ANA, "tipo": "processo", "numero_processo": "1003686-49.2015.8.26.0586"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertNotIn("dataDisponibilizacaoInicio", fonte.chamadas[0])

    def test_numero_com_dv_errado_nao_consulta_o_djen(self):
        cliente, _banco, fonte = montar()
        r = cliente.post("/prazos/monitoramentos",
                         json={"user_id": ANA, "tipo": "processo", "numero_processo": "1003686-48.2015.8.26.0586"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(fonte.chamadas, [])

    def test_outro_usuario_nao_ve_nem_altera(self):
        cliente, _banco, _fonte = montar([item_djen(1)])
        painel = cliente.post("/prazos/monitoramentos",
                              json={"user_id": ANA, "tipo": "oab", "oab_numero": "100000", "oab_uf": "SP"}).json()["painel"]
        pub_id = painel["publicacoes"][0]["id"]
        mon_id = painel["monitoramentos"][0]["id"]
        self.assertEqual(cliente.get("/prazos/painel", params={"user_id": BRUNO}).json()["publicacoes"], [])
        self.assertEqual(cliente.patch(f"/prazos/publicacoes/{pub_id}",
                                       json={"user_id": BRUNO, "situacao": "sem_prazo"}).status_code, 404)
        self.assertEqual(cliente.delete(f"/prazos/monitoramentos/{mon_id}", params={"user_id": BRUNO}).status_code, 404)
        self.assertEqual(cliente.post("/prazos/agenda", json={"user_id": BRUNO, "descricao": "x",
                                                              "data_final": "2026-12-01",
                                                              "publicacao_id": pub_id}).status_code, 404)

    def test_prazo_agendado_marca_a_intimacao_e_excluir_devolve_para_pendente(self):
        cliente, _banco, _fonte = montar([item_djen(1)])
        painel = cliente.post("/prazos/monitoramentos",
                              json={"user_id": ANA, "tipo": "oab", "oab_numero": "100000", "oab_uf": "SP"}).json()["painel"]
        pub_id = painel["publicacoes"][0]["id"]
        r = cliente.post("/prazos/agenda", json={"user_id": ANA, "descricao": "Réplica", "data_final": "2026-12-04",
                                                 "publicacao_id": pub_id})
        self.assertEqual(r.status_code, 200, r.text)
        prazo = r.json()["prazo"]
        self.assertEqual((prazo["numeroProcesso"], prazo["dataFinal"]), (PROCESSO, "2026-12-04"))
        painel = cliente.get("/prazos/painel", params={"user_id": ANA}).json()
        self.assertEqual(painel["publicacoes"][0]["situacao"], "agendada")
        self.assertEqual(cliente.patch(f"/prazos/publicacoes/{pub_id}",
                                       json={"user_id": ANA, "situacao": "sem_prazo"}).status_code, 409)

        cumprido = cliente.patch(f"/prazos/agenda/{prazo['id']}", json={"user_id": ANA, "cumprido": True}).json()
        self.assertTrue(cumprido["prazo"]["cumprido"])
        self.assertEqual(cliente.delete(f"/prazos/agenda/{prazo['id']}", params={"user_id": ANA}).status_code, 204)
        painel = cliente.get("/prazos/painel", params={"user_id": ANA}).json()
        self.assertEqual(painel["publicacoes"][0]["situacao"], "pendente")
        self.assertEqual(painel["prazos"], [])

    def test_data_final_invalida_e_recusada(self):
        cliente, _banco, _fonte = montar()
        r = cliente.post("/prazos/agenda", json={"user_id": ANA, "descricao": "x", "data_final": "2026-02-30"})
        self.assertEqual(r.status_code, 400)

    def test_caso_aceita_so_processo_e_so_do_dono(self):
        cliente, _banco, _fonte = montar()
        oab = cliente.post("/prazos/monitoramentos", json={"user_id": ANA, "tipo": "oab", "oab_numero": "1",
                                                           "oab_uf": "SP", "caso_id": "caso-ana"})
        self.assertEqual(oab.status_code, 400)
        alheio = cliente.post("/prazos/monitoramentos", json={"user_id": BRUNO, "tipo": "processo",
                                                              "numero_processo": PROCESSO, "caso_id": "caso-ana"})
        self.assertEqual(alheio.status_code, 404)

    def test_painel_do_caso_mostra_so_o_processo_dele_e_prazo_herda_o_caso(self):
        cliente, _banco, _fonte = montar([item_djen(1), item_djen(2, OUTRO_PROCESSO)])
        # Pela OAB chegam as duas intimações; o caso só acompanha um dos processos.
        cliente.post("/prazos/monitoramentos", json={"user_id": ANA, "tipo": "oab", "oab_numero": "100000",
                                                     "oab_uf": "SP"})
        r = cliente.post("/prazos/monitoramentos", json={"user_id": ANA, "tipo": "processo",
                                                         "numero_processo": PROCESSO, "caso_id": "caso-ana"})
        self.assertEqual(r.status_code, 200, r.text)
        painel_caso = r.json()["painel"]
        self.assertEqual([p["numeroProcesso"] for p in painel_caso["publicacoes"]], [PROCESSO])
        self.assertEqual(len(painel_caso["monitoramentos"]), 1)

        geral = cliente.get("/prazos/painel", params={"user_id": ANA}).json()
        da_oab = next(p for p in geral["publicacoes"] if p["numeroProcesso"] == PROCESSO)
        prazo = cliente.post("/prazos/agenda", json={"user_id": ANA, "descricao": "Contestação",
                                                     "data_final": "2026-12-01", "publicacao_id": da_oab["id"]}).json()
        self.assertEqual(prazo["prazo"]["casoId"], "caso-ana")
        painel_caso = cliente.get("/prazos/painel", params={"user_id": ANA, "caso_id": "caso-ana"}).json()
        self.assertEqual(len(painel_caso["prazos"]), 1)

    def test_processo_de_outro_caso_responde_409(self):
        cliente, _banco, _fonte = montar(casos={(ANA, "caso-ana"), (ANA, "caso-2")})
        corpo = {"user_id": ANA, "tipo": "processo", "numero_processo": PROCESSO}
        cliente.post("/prazos/monitoramentos", json={**corpo, "caso_id": "caso-ana"})
        self.assertEqual(cliente.post("/prazos/monitoramentos", json={**corpo, "caso_id": "caso-2"}).status_code, 409)

    def test_sincronizar_respeita_intervalo_e_repete_alguns_dias(self):
        cliente, banco, fonte = montar([item_djen(1)])
        cliente.post("/prazos/monitoramentos", json={"user_id": ANA, "tipo": "oab", "oab_numero": "100000",
                                                     "oab_uf": "SP"})
        fonte.chamadas.clear()
        automatico = cliente.post("/prazos/sincronizar", json={"user_id": ANA}).json()
        self.assertEqual(automatico["consultados"], 0)

        # Simula a última sincronização há 2 minutos: o "Atualizar agora" consulta de novo.
        mon = banco["monitoramentos"].docs[0]
        antes = router.agora() - timedelta(minutes=2)
        mon["ultima_sincronizacao"] = antes.isoformat()
        fonte.itens.append(item_djen(3))
        forcado = cliente.post("/prazos/sincronizar", json={"user_id": ANA, "forcar": True}).json()
        self.assertEqual((forcado["consultados"], forcado["novas"]), (1, 1))
        esperado = (antes.date() - timedelta(days=router.SOBREPOSICAO_DIAS)).isoformat()
        self.assertEqual(fonte.chamadas[0]["dataDisponibilizacaoInicio"], esperado)
        self.assertEqual(len(forcado["painel"]["publicacoes"]), 2)

    def test_limite_do_djen_para_a_sincronizacao_e_fica_registrado(self):
        cliente, banco, fonte = montar()
        fonte.status = 429
        r = cliente.post("/prazos/monitoramentos", json={"user_id": ANA, "tipo": "oab", "oab_numero": "100000",
                                                         "oab_uf": "SP"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("limitou", r.json()["aviso"])
        mon = r.json()["painel"]["monitoramentos"][0]
        self.assertIn("limitou", mon["ultimoErro"])
        self.assertIsNone(banco["monitoramentos"].docs[0].get("ultima_tentativa"))

    def test_remover_monitoramento_apaga_so_o_que_ninguem_tratou(self):
        cliente, banco, _fonte = montar([item_djen(1), item_djen(2, OUTRO_PROCESSO)])
        painel = cliente.post("/prazos/monitoramentos", json={"user_id": ANA, "tipo": "oab",
                                                              "oab_numero": "100000", "oab_uf": "SP"}).json()["painel"]
        agendar = painel["publicacoes"][0]["id"]
        cliente.post("/prazos/agenda", json={"user_id": ANA, "descricao": "x", "data_final": "2026-12-01",
                                             "publicacao_id": agendar})
        mon_id = painel["monitoramentos"][0]["id"]
        self.assertEqual(cliente.delete(f"/prazos/monitoramentos/{mon_id}", params={"user_id": ANA}).status_code, 204)
        restantes = banco["publicacoes"].docs
        self.assertEqual([str(p["_id"]) for p in restantes], [agendar])
        self.assertEqual(len(banco["prazos"].docs), 1)

    def test_painel_resume_o_teor_longo_e_o_inteiro_teor_vem_a_parte(self):
        longo = item_djen(1, texto="<p>" + "Vistos. " * 600 + "</p>")
        cliente, _banco, _fonte = montar([longo])
        painel = cliente.post("/prazos/monitoramentos", json={"user_id": ANA, "tipo": "oab", "oab_numero": "100000",
                                                              "oab_uf": "SP"}).json()["painel"]
        resumida = painel["publicacoes"][0]
        self.assertTrue(resumida["textoTruncado"])
        self.assertLessEqual(len(resumida["texto"]), router.RESUMO_TEXTO)
        inteira = cliente.get(f"/prazos/publicacoes/{resumida['id']}", params={"user_id": ANA}).json()["publicacao"]
        self.assertFalse(inteira["textoTruncado"])
        self.assertGreater(len(inteira["texto"]), 4000)
        self.assertEqual(cliente.get(f"/prazos/publicacoes/{resumida['id']}",
                                     params={"user_id": BRUNO}).status_code, 404)

    def test_limite_de_acompanhamentos(self):
        cliente, banco, _fonte = montar()
        for i in range(router.MAX_MONITORAMENTOS):
            banco["monitoramentos"].docs.append({"_id": ObjectId(), "user_id": ANA, "tipo": "oab", "chave": f"oab:{i}/SP",
                                                 "criado_em": "2026-01-01T00:00:00", "ultima_sincronizacao": "x"})
        r = cliente.post("/prazos/monitoramentos", json={"user_id": ANA, "tipo": "oab", "oab_numero": "999",
                                                         "oab_uf": "SP"})
        self.assertEqual(r.status_code, 409)


if __name__ == "__main__":
    unittest.main()
