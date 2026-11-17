"""Transcrição e revisão: em produção (Vercel) só OpenAI; Groq e Whisper local só na máquina.
Sem rede: as APIs de transcrição são simuladas com httpx.MockTransport.
Rodar em backend/:  python -m unittest discover -s tests -v
"""
import asyncio
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

SEM_CHAVES = {"OPENAI_API_KEY": "", "GROQ_API_KEY": "", "VERCEL": ""}
# A classe de verdade, guardada antes de o teste trocar httpx.AsyncClient pela falsa.
CLIENTE_HTTPX = httpx.AsyncClient


class ApiFalsa:
    """Responde como a API de transcrição e guarda os pedidos recebidos."""

    def __init__(self, texto="Texto transcrito.", status=200):
        self.pedidos, self.texto, self.status = [], texto, status

    def __call__(self, pedido: httpx.Request) -> httpx.Response:
        self.pedidos.append(pedido)
        if self.status != 200:
            return httpx.Response(self.status, text="erro da api")
        return httpx.Response(200, json={"text": self.texto})

    def cliente(self, **kwargs):
        return CLIENTE_HTTPX(transport=httpx.MockTransport(self), **kwargs)


def ambiente(**valores):
    return patch.dict(os.environ, {**SEM_CHAVES, **valores})


class QualServico(unittest.TestCase):
    def test_com_a_chave_da_openai_usa_a_openai_mesmo_havendo_groq(self):
        with ambiente(OPENAI_API_KEY="sk-x", GROQ_API_KEY="gsk_x", VERCEL="1"):
            self.assertEqual(main.servico_de_transcricao(), "openai")
        with ambiente(OPENAI_API_KEY="sk-x", GROQ_API_KEY="gsk_x"):
            self.assertEqual(main.servico_de_transcricao(), "openai")

    def test_na_vercel_a_groq_nunca_e_usada(self):
        with ambiente(GROQ_API_KEY="gsk_x", VERCEL="1"):
            self.assertEqual(main.servico_de_transcricao(), "")
        with ambiente(VERCEL="1"):
            self.assertEqual(main.servico_de_transcricao(), "")

    def test_na_maquina_sem_openai_usa_groq_ou_whisper_local(self):
        with ambiente(GROQ_API_KEY="gsk_x"):
            self.assertEqual(main.servico_de_transcricao(), "groq")
        with ambiente():
            self.assertEqual(main.servico_de_transcricao(), "local")


class Transcrever(unittest.TestCase):
    def transcrever(self, api, **env):
        with ambiente(**env), patch.object(main.httpx, "AsyncClient", api.cliente):
            return asyncio.run(main.transcrever_audio(b"audio", "gravacao.webm"))

    def test_openai_com_whisper_1_em_portugues(self):
        api = ApiFalsa("  O cliente trabalhou de 2019 a 2024.  ")
        texto = self.transcrever(api, OPENAI_API_KEY="sk-teste", GROQ_API_KEY="gsk_x", VERCEL="1")
        self.assertEqual(texto, "O cliente trabalhou de 2019 a 2024.")
        [pedido] = api.pedidos
        self.assertEqual(str(pedido.url), "https://api.openai.com/v1/audio/transcriptions")
        self.assertEqual(pedido.headers["authorization"], "Bearer sk-teste")
        corpo = pedido.content.decode("utf-8", "replace")
        for campo, valor in (("model", "whisper-1"), ("language", "pt"), ("response_format", "json")):
            self.assertIn(f'name="{campo}"\r\n\r\n{valor}', corpo)

    def test_na_vercel_sem_openai_avisa_e_nao_chama_ninguem(self):
        api = ApiFalsa()
        with self.assertRaises(main.TranscricaoErro) as erro:
            self.transcrever(api, GROQ_API_KEY="gsk_x", VERCEL="1")
        self.assertEqual(erro.exception.status, 503)
        self.assertIn("OPENAI_API_KEY", str(erro.exception))
        self.assertEqual(api.pedidos, [])

    def test_groq_so_na_maquina_sem_openai(self):
        api = ApiFalsa()
        self.transcrever(api, GROQ_API_KEY="gsk_x")
        self.assertIn("api.groq.com", str(api.pedidos[0].url))

    def test_audio_acima_de_25_mb_e_erro_de_api_viram_mensagem(self):
        api = ApiFalsa()
        with ambiente(OPENAI_API_KEY="sk-x"), patch.object(main.httpx, "AsyncClient", api.cliente):
            with self.assertRaises(main.TranscricaoErro) as grande:
                asyncio.run(main.transcrever_audio(b"x" * (main.LIMITE_AUDIO + 1), "a.webm"))
        self.assertEqual(grande.exception.status, 413)
        with self.assertRaises(main.TranscricaoErro) as falha:
            self.transcrever(ApiFalsa(status=401), OPENAI_API_KEY="sk-x")
        self.assertIn("OpenAI", str(falha.exception))

    def test_rota_transcribe_devolve_o_texto(self):
        api = ApiFalsa("Olá, doutora.")
        with ambiente(OPENAI_API_KEY="sk-x", VERCEL="1"), patch.object(main.httpx, "AsyncClient", api.cliente):
            r = TestClient(main.app).post("/transcribe", files={"audio": ("g.webm", b"audio", "audio/webm")})
        self.assertEqual(r.json(), {"text": "Olá, doutora."})


class Revisao(unittest.TestCase):
    def test_sempre_pelo_provedor_da_analise_e_ignora_chave_da_groq_no_pedido(self):
        class Ia:
            prompts = []

            def generate(self, sistema, texto, busca, json_mode):
                self.prompts.append((texto, busca, json_mode))
                return " Texto revisado. "

        ia = Ia()
        with patch.object(main, "provider_do_servidor", lambda: ia):
            r = TestClient(main.app).post(
                "/revisar-transcricao", json={"texto": "texto cru", "groq_api_key": "gsk_x"}
            )
        self.assertEqual(r.json(), {"texto_revisado": "Texto revisado."})
        self.assertEqual(ia.prompts, [("texto cru", False, False)])

    def test_health_mostra_a_transcricao_pela_openai(self):
        with ambiente(OPENAI_API_KEY="sk-x", VERCEL="1"), patch.object(main, "mongo_client", None):
            dados = TestClient(main.app).get("/health").json()
        self.assertEqual(dados["transcricao"], "openai (whisper-1)")
        self.assertNotIn("groq", dados)


if __name__ == "__main__":
    unittest.main()
