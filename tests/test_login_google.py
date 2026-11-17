"""Login com Google sem rede e sem MongoDB: tokens assinados com uma chave RSA de teste
no lugar das chaves do Google. Rodar em backend/:  python -m unittest discover -s tests -v
"""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import bcrypt  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from google.auth import crypt  # noqa: E402
from google.auth import jwt as jwt_google  # noqa: E402

import login_google  # noqa: E402
from login_google import LoginGoogleIndisponivel, TokenGoogleInvalido, verificar_credencial  # noqa: E402

CLIENTE = "sophia-teste.apps.googleusercontent.com"
NONCE = "nonce-bruto-do-cookie"


def _par_de_chaves():
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    privada = chave.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    publica = chave.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    return privada, publica


CHAVE, PUBLICA = _par_de_chaves()
CHAVE_DE_OUTRO, _ = _par_de_chaves()
CERTIFICADOS = {"k1": PUBLICA}


def token(chave=CHAVE, kid="k1", **mudancas):
    """ID token como o do Google; `campo=None` tira o campo."""
    agora = int(time.time())
    dados = {
        "iss": "https://accounts.google.com",
        "aud": CLIENTE,
        "sub": "109876543210",
        "email": "Ana.Souza@Gmail.com",
        "email_verified": True,
        "name": "Ana Souza",
        "iat": agora,
        "exp": agora + 3600,
        "nonce": login_google.hash_do_nonce(NONCE),
    }
    dados.update(mudancas)
    dados = {k: v for k, v in dados.items() if v is not None}
    return jwt_google.encode(crypt.RSASigner.from_string(chave, key_id=kid), dados).decode()


def _b64(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode()


class ComGoogleFalso(unittest.TestCase):
    """GOOGLE_CLIENT_ID de teste e chaves do Google trocadas pela chave local."""

    def setUp(self):
        self.certificados = AsyncMock(return_value=CERTIFICADOS)
        for alvo in (
            patch.dict(os.environ, {"GOOGLE_CLIENT_ID": CLIENTE}),
            patch.object(login_google, "certificados_do_google", self.certificados),
        ):
            alvo.start()
            self.addCleanup(alvo.stop)


class VerificarCredencial(ComGoogleFalso):
    def conferir(self, credencial, nonce=NONCE):
        return asyncio.run(verificar_credencial(credencial, nonce))

    def recusa(self, credencial, nonce=NONCE):
        with self.assertRaises(TokenGoogleInvalido):
            self.conferir(credencial, nonce)

    def test_token_valido_devolve_a_conta_com_email_minusculo(self):
        self.assertEqual(
            self.conferir(token()),
            {"sub": "109876543210", "email": "ana.souza@gmail.com", "nome": "Ana Souza"},
        )

    def test_aceita_emissor_sem_https_e_mais_de_um_client_id(self):
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": f"outro-ambiente, {CLIENTE}"}):
            self.assertEqual(self.conferir(token(iss="accounts.google.com"))["sub"], "109876543210")

    def test_recusa_assinatura_de_outra_chave(self):
        self.recusa(token(chave=CHAVE_DE_OUTRO))

    def test_recusa_token_de_outro_app(self):
        self.recusa(token(aud="app-de-outra-pessoa.apps.googleusercontent.com"))

    def test_recusa_token_vencido_e_do_futuro(self):
        agora = int(time.time())
        self.recusa(token(iat=agora - 7200, exp=agora - 3600))
        self.recusa(token(iat=agora + 3600, exp=agora + 7200))

    def test_recusa_emissor_que_nao_e_o_google(self):
        self.recusa(token(iss="https://accounts.google.com.golpe.com"))

    def test_recusa_email_nao_verificado_ou_ausente(self):
        self.recusa(token(email_verified=False))
        self.recusa(token(email_verified=None))
        self.recusa(token(email=None))

    def test_recusa_nonce_de_outra_tentativa(self):
        self.recusa(token(), nonce="outro-nonce")
        self.recusa(token(), nonce="")
        self.recusa(token(nonce=None))
        # Quem só tem o token vê o hash do nonce; mandar o hash no lugar do valor bruto não passa.
        self.recusa(token(), nonce=login_google.hash_do_nonce(NONCE))

    def test_recusa_algoritmo_trocado(self):
        """Ataque clássico: HS256 usando a chave pública como segredo, ou `alg: none`."""
        agora = int(time.time())
        corpo = _b64(json.dumps({
            "iss": "https://accounts.google.com", "aud": CLIENTE, "sub": "1", "email": "a@b.com",
            "email_verified": True, "iat": agora, "exp": agora + 3600,
            "nonce": login_google.hash_do_nonce(NONCE),
        }).encode())
        for alg in ("HS256", "none"):
            cabecalho = _b64(json.dumps({"alg": alg, "kid": "k1", "typ": "JWT"}).encode())
            assinatura = hmac.new(PUBLICA.encode(), f"{cabecalho}.{corpo}".encode(), hashlib.sha256).digest()
            self.recusa(f"{cabecalho}.{corpo}.{_b64(assinatura) if alg != 'none' else ''}")

    def test_recusa_lixo_e_token_gigante(self):
        self.recusa("isso-nao-e-um-jwt")
        self.recusa("")
        self.recusa(token() + "a" * 5000)

    def test_chave_desconhecida_busca_as_chaves_de_novo_uma_vez(self):
        self.recusa(token(kid="chave-nova"))
        self.assertEqual(self.certificados.await_args_list[-1].kwargs, {"forcar": True})
        self.assertEqual(self.certificados.await_count, 2)

    def test_sem_client_id_o_login_fica_desligado(self):
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": ""}):
            with self.assertRaises(LoginGoogleIndisponivel):
                self.conferir(token())

    def test_validade_do_cache_segue_o_google_com_teto(self):
        self.assertEqual(login_google._validade("public, max-age=21000, must-revalidate"), 21000)
        self.assertEqual(login_google._validade(""), 3600)
        self.assertEqual(login_google._validade("max-age=99999999"), 86400)


class RotasDoLogin(ComGoogleFalso):
    """/entrar/google, /entrar/google/vincular e o efeito em /entrar e /cadastro (usuários num arquivo)."""

    def setUp(self):
        super().setUp()
        import main

        self.main = main
        self.usuarios = []
        originais = main.users_collection, main._ler_users_arquivo, main._gravar_users_arquivo
        main.users_collection = None
        main._ler_users_arquivo = lambda: self.usuarios
        main._gravar_users_arquivo = lambda lista: None
        self.addCleanup(lambda: setattr(main, "users_collection", originais[0]))
        self.addCleanup(lambda: setattr(main, "_ler_users_arquivo", originais[1]))
        self.addCleanup(lambda: setattr(main, "_gravar_users_arquivo", originais[2]))
        self.c = TestClient(main.app)

    def entrar_google(self, credencial=None, nonce=NONCE):
        return self.c.post("/entrar/google", json={"credencial": credencial or token(), "nonce": nonce})

    def conta_com_senha(self, email="ana.souza@gmail.com", senha="senha-certa-123"):
        conta = {
            "_id": "conta-antiga", "name": "Ana", "email": email,
            "password_hash": bcrypt.hashpw(senha.encode(), bcrypt.gensalt(4)).decode(),
        }
        self.usuarios.append(conta)
        return conta

    def test_primeiro_login_cria_a_conta_e_o_segundo_entra_nela(self):
        r = self.entrar_google()
        self.assertEqual(r.status_code, 200, r.text)
        corpo = r.json()
        self.assertTrue(corpo["conta_nova"])
        self.assertEqual(corpo["usuario"]["email"], "ana.souza@gmail.com")
        self.assertEqual(corpo["usuario"]["name"], "Ana Souza")
        self.assertIsNone(corpo["usuario"]["terms_accepted_at"])
        self.assertNotIn("google_sub", corpo["usuario"])
        [salvo] = self.usuarios
        self.assertEqual(salvo["google_sub"], "109876543210")
        self.assertNotIn("password_hash", salvo)

        de_novo = self.entrar_google().json()
        self.assertEqual(de_novo["usuario"]["_id"], salvo["_id"])
        self.assertNotIn("conta_nova", de_novo)
        self.assertEqual(len(self.usuarios), 1)

    def test_token_invalido_nao_cria_nada(self):
        r = self.entrar_google(token(aud="outro-app"))
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["codigo"], "token_invalido")
        self.assertEqual(self.entrar_google(nonce="outro").status_code, 401)
        self.assertEqual(self.usuarios, [])

    def test_sem_client_id_responde_503(self):
        with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": ""}):
            self.assertEqual(self.entrar_google().status_code, 503)

    def test_conta_com_senha_so_liga_ao_google_com_a_senha(self):
        conta = self.conta_com_senha()
        r = self.entrar_google()
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["codigo"], "vincular_conta")
        self.assertNotIn("google_sub", conta)

        vincular = lambda senha: self.c.post(  # noqa: E731
            "/entrar/google/vincular", json={"credencial": token(), "nonce": NONCE, "senha": senha}
        )
        self.assertEqual(vincular("senha-errada").status_code, 401)
        self.assertEqual(vincular("x" * 100).status_code, 401)
        self.assertNotIn("google_sub", conta)

        r = vincular("senha-certa-123")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["usuario"]["_id"], "conta-antiga")
        self.assertEqual(conta["google_sub"], "109876543210")
        # Daqui para frente entra direto com o Google, e a senha continua valendo.
        self.assertEqual(self.entrar_google().json()["usuario"]["_id"], "conta-antiga")
        r = self.c.post("/entrar", json={"email": "ana.souza@gmail.com", "senha": "senha-certa-123"})
        self.assertEqual(r.status_code, 200)

    def test_vincular_exige_token_valido_mesmo_com_a_senha_certa(self):
        conta = self.conta_com_senha()
        r = self.c.post("/entrar/google/vincular", json={
            "credencial": token(chave=CHAVE_DE_OUTRO), "nonce": NONCE, "senha": "senha-certa-123",
        })
        self.assertEqual(r.status_code, 401)
        self.assertNotIn("google_sub", conta)

    def test_email_ja_ligado_a_outra_conta_google(self):
        self.usuarios.append({"_id": "x", "email": "ana.souza@gmail.com", "google_sub": "outro-sub"})
        self.assertEqual(self.entrar_google().status_code, 409)

    def test_conta_so_google_nao_entra_com_senha_e_nao_recadastra(self):
        self.entrar_google()
        r = self.c.post("/entrar", json={"email": "ana.souza@gmail.com", "senha": "qualquer-senha"})
        self.assertEqual(r.status_code, 401)
        self.assertIn("Google", r.json()["erro"])
        r = self.c.post("/cadastro", json={"nome": "Ana", "email": "ana.souza@gmail.com", "senha": "12345678"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("Google", r.json()["erro"])

    def test_banco_fora_do_ar_responde_503_com_a_mensagem_do_atlas(self):
        from pymongo.errors import ServerSelectionTimeoutError

        async def fora_do_ar(*_):
            raise ServerSelectionTimeoutError("cluster: timed out")

        with patch.object(self.main, "_usuario_por", fora_do_ar):
            for rota, extra in (("/entrar/google", {}), ("/entrar/google/vincular", {"senha": "x"})):
                r = self.c.post(rota, json={"credencial": token(), "nonce": NONCE, **extra})
                self.assertEqual(r.status_code, 503, rota)
                self.assertEqual(r.json()["erro"], self.main.MENSAGEM_BANCO_INDISPONIVEL)

    def test_senha_acima_de_72_bytes_nao_vira_erro_500(self):
        self.conta_com_senha(email="b@b.com")
        r = self.c.post("/entrar", json={"email": "b@b.com", "senha": "ç" * 50})
        self.assertEqual(r.status_code, 401)
        r = self.c.post("/cadastro", json={"nome": "B", "email": "c@c.com", "senha": "a" * 73})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
