"""
Login com Google: confere o ID token (JWT) que o botão do Google entrega ao navegador.

O navegador nunca é a fonte da verdade. Só aceitamos o token se:
- a assinatura confere com as chaves públicas do Google;
- foi emitido pelo Google (`iss`) para o nosso app (`aud` = GOOGLE_CLIENT_ID);
- não expirou (`exp`, `iat`, com 60 s de folga no relógio);
- o Google confirma que o email é da pessoa (`email_verified`);
- carrega o nonce desta tentativa de login.

O nonce bruto fica num cookie httpOnly do Next; o botão do Google recebe só o hash
(SHA-256). Quem copiar o token não tem o nonce bruto, então não consegue usá-lo aqui.
"""

import base64
import hashlib
import hmac
import os
import re
import time

import httpx
from google.auth import exceptions as erros_google
from google.auth import jwt as jwt_google

URL_CERTIFICADOS = "https://www.googleapis.com/oauth2/v1/certs"
EMISSORES = ("accounts.google.com", "https://accounts.google.com")
FOLGA_DO_RELOGIO = 60
# Um ID token do Google tem ~1 KB; o limite só barra lixo antes de decodificar.
TAMANHO_MAXIMO = 4096


class LoginGoogleIndisponivel(Exception):
    """GOOGLE_CLIENT_ID não configurado ou chaves do Google fora do ar."""


class TokenGoogleInvalido(Exception):
    """Token falso, vencido, de outro app, sem email verificado ou de outra tentativa."""


def ids_de_cliente() -> list[str]:
    """GOOGLE_CLIENT_ID aceita mais de um id separado por vírgula (ex.: um por ambiente)."""
    return [c.strip() for c in os.getenv("GOOGLE_CLIENT_ID", "").split(",") if c.strip()]


def hash_do_nonce(nonce: str) -> str:
    """Mesmo cálculo do Next: SHA-256 em base64url, sem `=`."""
    digest = hashlib.sha256(nonce.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


_cache = {"certificados": {}, "expira": 0.0}


def _validade(cache_control: str) -> int:
    achado = re.search(r"max-age=(\d+)", cache_control or "")
    return min(int(achado.group(1)), 86400) if achado else 3600


async def certificados_do_google(forcar: bool = False) -> dict[str, str]:
    """Chaves públicas do Google (kid -> certificado PEM), guardadas pelo tempo que o Google indica."""
    if not forcar and _cache["certificados"] and time.time() < _cache["expira"]:
        return _cache["certificados"]
    try:
        async with httpx.AsyncClient(timeout=5) as cliente:
            resposta = await cliente.get(URL_CERTIFICADOS)
            resposta.raise_for_status()
            certificados = resposta.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise LoginGoogleIndisponivel("Não foi possível buscar as chaves do Google.") from exc
    if not isinstance(certificados, dict) or not certificados:
        raise LoginGoogleIndisponivel("Resposta inesperada das chaves do Google.")
    _cache["certificados"] = certificados
    _cache["expira"] = time.time() + _validade(resposta.headers.get("cache-control", ""))
    return certificados


async def verificar_credencial(credencial: str, nonce: str) -> dict:
    """Devolve `{sub, email, nome}` do token conferido; senão levanta `TokenGoogleInvalido`."""
    clientes = ids_de_cliente()
    if not clientes:
        raise LoginGoogleIndisponivel("GOOGLE_CLIENT_ID não configurado.")
    credencial = (credencial or "").strip()
    if not credencial or len(credencial) > TAMANHO_MAXIMO or not nonce:
        raise TokenGoogleInvalido("Credencial ausente.")

    try:
        cabecalho = jwt_google.decode_header(credencial)
    except (ValueError, erros_google.GoogleAuthError) as exc:
        raise TokenGoogleInvalido("Credencial malformada.") from exc
    # O Google assina com RS256; qualquer outro algoritmo no cabeçalho é recusado.
    if cabecalho.get("alg") != "RS256" or not cabecalho.get("kid"):
        raise TokenGoogleInvalido("Algoritmo inesperado.")

    certificados = await certificados_do_google()
    if cabecalho["kid"] not in certificados:
        # O Google troca as chaves de tempos em tempos: busca de novo uma vez.
        certificados = await certificados_do_google(forcar=True)

    try:
        dados = jwt_google.decode(
            credencial,
            certs=certificados,
            audience=clientes,
            clock_skew_in_seconds=FOLGA_DO_RELOGIO,
        )
    except (ValueError, erros_google.GoogleAuthError) as exc:
        raise TokenGoogleInvalido("Assinatura, validade ou destinatário não conferem.") from exc

    if dados.get("iss") not in EMISSORES:
        raise TokenGoogleInvalido("Emissor desconhecido.")
    email = (dados.get("email") or "").strip().lower()
    if not dados.get("sub") or not email:
        raise TokenGoogleInvalido("Token sem conta.")
    if dados.get("email_verified") not in (True, "true"):
        raise TokenGoogleInvalido("Email não verificado pelo Google.")
    if not hmac.compare_digest(str(dados.get("nonce") or ""), hash_do_nonce(nonce)):
        raise TokenGoogleInvalido("Nonce não confere.")

    return {"sub": str(dados["sub"]), "email": email, "nome": (dados.get("name") or "").strip()[:150]}
