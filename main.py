"""
Sophia — API (cadastro + transcrição).
O modelo Whisper só é carregado na primeira transcrição, para o cadastro
funcionar sem esperar o download/carga do modelo.
"""

import asyncio
import io
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import httpx
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from analise.document_utils import extract_text
from analise.router import criar_router as criar_router_analise
from analise.storage import Armazenamento

PASTA_BACK = Path(__file__).resolve().parent
# override: o .env do backend vale mesmo se a variável já chegou vazia no processo.
load_dotenv(PASTA_BACK / ".env", override=True)
load_dotenv(PASTA_BACK.parent / ".env.local")
load_dotenv(PASTA_BACK.parent / ".env")

app = FastAPI(title="Sophia — API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGODB_URI = os.getenv("MONGODB_URI")
mongo_client = AsyncIOMotorClient(MONGODB_URI) if MONGODB_URI else None
mongo_db = mongo_client["sophia-data"] if mongo_client else None
users_collection = mongo_db["users"] if mongo_db is not None else None
case_collection = mongo_db["case"] if mongo_db is not None else None
# Análises, chat e minutas (módulo `analise`), cada um na sua coleção. Relatos e documentos ficam só em `case`.
armazenamento_ia = Armazenamento(mongo_db) if mongo_db is not None else None
USERS_FILE = PASTA_BACK / "data" / "users.json"
CASES_FILE = PASTA_BACK / "data" / "cases.json"
STATUS_CASO = {"gravacao_pendente", "em_analise", "concluido"}
PASTAS_CASO = {"ativo", "arquivo"}
AREAS_JURIDICAS = {
    "civil",
    "familia-sucessoes",
    "trabalhista",
    "previdenciario",
    "consumidor",
    "empresarial",
    "tributario",
    "penal",
    "administrativo",
    "imobiliario",
    "ambiental",
    "digital",
}
FUSO = timezone(timedelta(hours=-3))


def agora_iso() -> str:
    # Horário de Brasília em formato limpo (ex.: 2026-10-20T17:25:00).
    return datetime.now(FUSO).strftime("%Y-%m-%dT%H:%M:%S")

MODEL_SIZE = "small"
_whisper = None
OVERLAP_SECONDS = 1.0
SALVAR_AUDIO_DEBUG = False
PASTA_DEBUG = str(PASTA_BACK / "debug_audio")


def _garantir_compat_av() -> None:
    """Versões novas do PyAV (av>=16) removeram o argumento ``metadata_errors``
    de ``av.open``, mas o faster-whisper ainda o envia ao decodificar o áudio.
    Envolvemos ``av.open`` para descartar esse argumento quando ele não existir,
    evitando o erro 500 na transcrição."""
    import av

    if getattr(av.open, "_sophia_compat", False):
        return

    _open_original = av.open

    def open_compat(*args, **kwargs):
        try:
            return _open_original(*args, **kwargs)
        except TypeError:
            kwargs.pop("metadata_errors", None)
            return _open_original(*args, **kwargs)

    open_compat._sophia_compat = True
    av.open = open_compat


def obter_whisper():
    """Carrega o modelo só quando alguém transcreve — o cadastro não depende disso."""
    global _whisper
    if _whisper is None:
        _garantir_compat_av()
        from faster_whisper import WhisperModel

        _whisper = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _whisper


def transcrever_bloco(audio_bytes: bytes) -> str:
    if SALVAR_AUDIO_DEBUG:
        os.makedirs(PASTA_DEBUG, exist_ok=True)
        nome_arquivo = os.path.join(PASTA_DEBUG, f"bloco_{time.time():.0f}.wav")
        with open(nome_arquivo, "wb") as f:
            f.write(audio_bytes)
        print(f"[debug] áudio salvo em: {nome_arquivo}")

    audio_buffer = io.BytesIO(audio_bytes)
    segments, info = obter_whisper().transcribe(
        audio_buffer,
        language="pt",
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        word_timestamps=True,
    )
    segments = list(segments)

    palavras = []
    for seg in segments:
        if not seg.words:
            continue
        for w in seg.words:
            if w.start >= OVERLAP_SECONDS - 0.05:
                palavras.append(w.word)

    texto = "".join(palavras).strip()
    print(
        f"[debug] bytes_recebidos={len(audio_bytes)} "
        f"duracao_audio={info.duration:.2f}s "
        f"idioma_detectado={info.language} "
        f"confianca_idioma={info.language_probability:.2f} "
        f"n_segmentos={len(segments)} "
        f"texto={texto!r}"
    )
    return texto


def transcrever_audio_completo_sync(audio_bytes: bytes) -> str:
    if SALVAR_AUDIO_DEBUG:
        os.makedirs(PASTA_DEBUG, exist_ok=True)
        nome_arquivo = os.path.join(PASTA_DEBUG, f"completo_{time.time():.0f}.webm")
        with open(nome_arquivo, "wb") as f:
            f.write(audio_bytes)
        print(f"[debug] áudio completo salvo em: {nome_arquivo}")

    audio_buffer = io.BytesIO(audio_bytes)
    segments, info = obter_whisper().transcribe(
        audio_buffer,
        language="pt",
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    segments = list(segments)
    texto = " ".join(seg.text.strip() for seg in segments).strip()
    print(
        f"[debug] TRANSCRIÇÃO COMPLETA: "
        f"duracao_audio={info.duration:.2f}s "
        f"idioma_detectado={info.language} "
        f"n_segmentos={len(segments)} "
        f"tamanho_texto={len(texto)} caracteres"
    )
    return texto


@app.get("/")
async def raiz():
    return {"servico": "Sophia API", "health": "/health", "docs": "/docs"}


@app.get("/health")
async def health():
    mongo_status = "arquivo local (cole a MONGODB_URI do Atlas em backend/.env)"
    if mongo_client is not None:
        try:
            await mongo_client.admin.command("ping")
            mongo_status = "conectado"
        except Exception as exc:  # noqa: BLE001
            mongo_status = f"erro: {exc}"

    return {
        "status": "ok",
        "mongodb": mongo_status,
        "whisper": "pronto" if _whisper is not None else "ainda não carregado",
        "groq": "configurada" if os.getenv("GROQ_API_KEY", "").strip() else "ausente",
    }


@app.post("/transcribe")
async def transcrever_audio_completo(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    texto = await asyncio.to_thread(transcrever_audio_completo_sync, audio_bytes)
    return {"text": texto}


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-120b"

PROMPT_REVISAO = """Você está revisando a transcrição de uma entrevista jurídica \
entre um advogado e seu cliente, gerada por um sistema de reconhecimento de voz.

Sua única tarefa é corrigir erros PROVÁVEIS DE TRANSCRIÇÃO — palavras que soam \
parecido foneticamente com o que provavelmente foi dito, mas que não fazem \
sentido no contexto (ex: "tese de dano moral" transcrito errado como "tese \
de dano mural").

Regras estritas:
- NÃO resuma, NÃO reescreva o estilo, NÃO corrija gramática coloquial normal \
de fala.
- NÃO adicione informação nenhuma que não esteja no texto original.
- NÃO remova nada, mesmo que pareça irrelevante.
- Se não tiver certeza se algo é erro de transcrição, MANTENHA como está \
(prefira não mexer a inventar uma correção errada).
- Responda APENAS com o texto corrigido, sem comentários, sem explicações, \
sem aspas ao redor.

Texto a revisar:
"""


class RevisarTextoRequest(BaseModel):
    texto: str
    groq_api_key: str = ""


class CadastroRequest(BaseModel):
    nome: str
    email: str
    senha: str


class EntrarRequest(BaseModel):
    email: str
    senha: str


class CartaoAssinatura(BaseModel):
    brand: str = ""
    last4: str = ""
    expiry: str = ""
    holder_name: str = ""


class TrocaPlanoRequest(BaseModel):
    # user_id vem do cookie assinado, lido pela rota /api/assinatura/plano do Next.
    user_id: str
    plan_id: str


class CancelarContaRequest(BaseModel):
    # user_id vem do cookie assinado, lido pela rota /api/conta/cancelar do Next.
    user_id: str


class AssinaturaRequest(BaseModel):
    # user_id vem do cookie assinado, lido pela rota /api/assinatura do Next.
    user_id: str
    plan_id: str
    card: CartaoAssinatura


# Valores em centavos. O preço é sempre calculado aqui, nunca aceito do front.
PRECO_PLATAFORMA = 15000
PRECO_PLANOS = {"basico": 10000, "intermediario": 25000, "pro": 60000}
NOME_PLANOS = {"basico": "Básico", "intermediario": "Intermediário", "pro": "Pro"}


@app.post("/revisar-transcricao")
async def revisar_transcricao(payload: RevisarTextoRequest):
    if not payload.texto.strip():
        return {"texto_revisado": payload.texto}

    chave = payload.groq_api_key.strip() or os.getenv("GROQ_API_KEY", "")
    if not chave:
        return {
            "erro": (
                "Nenhuma chave da Groq informada (nem no pedido, "
                "nem em GROQ_API_KEY no .env do backend)."
            )
        }

    headers = {
        "Authorization": f"Bearer {chave}",
        "Content-Type": "application/json",
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": PROMPT_REVISAO},
            {"role": "user", "content": payload.texto},
        ],
        "temperature": 0.0,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resposta = await client.post(GROQ_API_URL, headers=headers, json=body)

    if resposta.status_code != 200:
        return {
            "erro": f"Groq retornou status {resposta.status_code}: {resposta.text}"
        }

    dados = resposta.json()
    texto_revisado = dados["choices"][0]["message"]["content"].strip()
    return {"texto_revisado": texto_revisado}


def usuario_publico(documento: dict) -> dict:
    return {
        "_id": documento["_id"],
        "name": documento.get("name") or "",
        "email": documento.get("email") or "",
        # Contas sem o campo ainda não pagaram a assinatura.
        "account_status": documento.get("account_status") or "pagamento_pendente",
        "created_at": documento.get("created_at") or "",
        # Ausente nas contas antigas: segue ativa. false = pediu cancelamento.
        "account_active": documento.get("account_active") is not False,
        "subscription": _resumo_assinatura_publico(documento.get("subscription")),
    }


def _resumo_assinatura_publico(resumo: dict | None) -> dict | None:
    """Plano e cartão para exibir na conta; o valor fica de fora de propósito."""
    if not resumo:
        return None
    return {
        "plan_id": resumo.get("plan_id") or "",
        "plan_name": resumo.get("plan_name") or "",
        "card": resumo.get("card") or {},
    }


def _ler_users_arquivo() -> list[dict]:
    if not USERS_FILE.exists():
        return []
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def _gravar_users_arquivo(lista: list[dict]) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(lista, indent=2, ensure_ascii=False), encoding="utf-8")


def _ler_cases_arquivo() -> list[dict]:
    if not CASES_FILE.exists():
        return []
    return json.loads(CASES_FILE.read_text(encoding="utf-8"))


def _gravar_cases_arquivo(lista: list[dict]) -> None:
    CASES_FILE.parent.mkdir(parents=True, exist_ok=True)
    CASES_FILE.write_text(json.dumps(lista, indent=2, ensure_ascii=False), encoding="utf-8")


def _id_do_caso(documento: dict) -> str:
    caso_id = str(documento.get("caso_id") or "").strip()
    if caso_id:
        return caso_id
    return str(documento.get("_id") or "")


def _mesmo_caso(documento: dict, caso_id: str) -> bool:
    return _id_do_caso(documento) == caso_id or str(documento.get("_id") or "") == caso_id


ORIGENS_TRANSCRIPT = {"audio", "manual"}


def _entradas_transcript(documento: dict) -> list[dict]:
    """`transcript` do caso como lista. Casos antigos guardam um objeto único: vira lista de um item."""
    bruto = documento.get("transcript")
    if isinstance(bruto, dict):
        bruto = [bruto]
    if not isinstance(bruto, list):
        return []
    return [item for item in bruto if isinstance(item, dict) and str(item.get("text") or "").strip()]


def _caso_publico(documento: dict) -> dict:
    texto = " ".join(str(item.get("text") or "").strip() for item in _entradas_transcript(documento))
    status = documento.get("status")
    if status not in STATUS_CASO:
        status = "em_analise" if texto else "gravacao_pendente"
    pasta = documento.get("folder") if documento.get("folder") in PASTAS_CASO else "ativo"
    return {
        "_id": _id_do_caso(documento),
        "title": str(documento.get("title") or "").strip() or "Caso sem título",
        "client_name": documento.get("client_name") or "",
        "legal_area": documento.get("legal_area") or None,
        "status": status,
        "folder": pasta,
        "updated_at": documento.get("updated_at") or documento.get("created_at") or "",
    }


def _caso_id_valido(caso_id: str) -> bool:
    return bool(caso_id) and len(caso_id) <= 120 and all(c.isalnum() or c in "-_" for c in caso_id)


@app.post("/cadastro")
async def cadastro(payload: CadastroRequest):
    """Cria um documento na collection users (UUID, email, bcrypt, created_at)."""
    nome = payload.nome.strip()
    email = payload.email.strip().lower()
    senha = payload.senha
    if not nome:
        return JSONResponse({"erro": "Informe o nome completo."}, status_code=400)
    if not email or "@" not in email:
        return JSONResponse({"erro": "Informe um email válido."}, status_code=400)
    if len(senha) < 8:
        return JSONResponse(
            {"erro": "A senha deve ter pelo menos 8 caracteres."},
            status_code=400,
        )

    if users_collection is not None:
        existente = await users_collection.find_one({"email": email})
    else:
        existente = next((u for u in _ler_users_arquivo() if u.get("email") == email), None)
    if existente:
        return JSONResponse({"erro": "Já existe uma conta com este email."}, status_code=400)

    user_id = str(uuid.uuid4())
    password_hash = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    documento = {
        "_id": user_id,
        "name": nome,
        "email": email,
        "password_hash": password_hash,
        "account_active": True,
        "created_at": agora_iso(),
    }
    try:
        if users_collection is not None:
            await users_collection.create_index("email", unique=True)
            await users_collection.insert_one(documento)
        else:
            lista = _ler_users_arquivo()
            lista.append(documento)
            _gravar_users_arquivo(lista)
    except Exception as exc:  # noqa: BLE001
        if "duplicate" in str(exc).lower():
            return JSONResponse({"erro": "Já existe uma conta com este email."}, status_code=400)
        return JSONResponse({"erro": str(exc)}, status_code=500)

    return {"usuario": {"_id": user_id, "name": nome, "email": email}}


@app.post("/entrar")
async def entrar(payload: EntrarRequest):
    email = payload.email.strip().lower()
    senha = payload.senha
    if not email or not senha:
        return JSONResponse({"erro": "Informe email e senha."}, status_code=400)

    if users_collection is not None:
        documento = await users_collection.find_one({"email": email})
    else:
        documento = next((u for u in _ler_users_arquivo() if u.get("email") == email), None)

    if not documento:
        return JSONResponse({"erro": "Email ou senha inválidos."}, status_code=401)

    hash_salvo = (documento.get("password_hash") or "").encode("utf-8")
    if not hash_salvo or not bcrypt.checkpw(senha.encode("utf-8"), hash_salvo):
        return JSONResponse({"erro": "Email ou senha inválidos."}, status_code=401)

    return {"usuario": usuario_publico(documento)}


async def _buscar_usuario(user_id: str) -> dict | None:
    if users_collection is not None:
        return await users_collection.find_one({"_id": user_id})
    return next((u for u in _ler_users_arquivo() if u.get("_id") == user_id), None)


@app.get("/usuario/{user_id}")
async def obter_usuario(user_id: str):
    """Dados públicos do usuário da sessão (o Next só chama com o id do cookie assinado)."""
    documento = await _buscar_usuario(user_id.strip())
    if not documento:
        return JSONResponse({"erro": "Usuário não encontrado."}, status_code=404)
    return {"usuario": usuario_publico(documento)}


@app.post("/assinatura")
async def assinar(payload: AssinaturaRequest):
    """Registra a assinatura do usuário e libera a conta (account_status = ativa)."""
    user_id = payload.user_id.strip()
    plano = payload.plan_id.strip()
    if plano not in PRECO_PLANOS:
        return JSONResponse({"erro": "Plano inválido."}, status_code=400)
    if not await _buscar_usuario(user_id):
        return JSONResponse({"erro": "Usuário não encontrado."}, status_code=404)

    agora = agora_iso()
    assinatura_id = str(uuid.uuid4())
    # Só o que pode aparecer no Mongo: bandeira, final, validade e nome.
    # Número completo, CVV e CPF não entram no documento.
    cartao = {
        "brand": payload.card.brand.strip() or "desconhecida",
        "last4": payload.card.last4[-4:],
        "expiry": payload.card.expiry.strip(),
        "holder_name": payload.card.holder_name.strip(),
    }
    documento = {
        "_id": assinatura_id,
        "user_id": user_id,
        "plan_id": plano,
        "plan_name": NOME_PLANOS[plano],
        "status": "ativa",
        "platform_amount": PRECO_PLATAFORMA,
        "plan_amount": PRECO_PLANOS[plano],
        "monthly_amount": PRECO_PLATAFORMA + PRECO_PLANOS[plano],
        "card": cartao,
        "created_at": agora,
    }
    assinatura_do_usuario = {
        "id": assinatura_id,
        "plan_id": plano,
        "plan_name": NOME_PLANOS[plano],
        "monthly_amount": documento["monthly_amount"],
        "card": {
            "brand": cartao["brand"],
            "last4": cartao["last4"],
            "expiry": cartao["expiry"],
        },
        "since": agora,
    }
    try:
        if users_collection is not None:
            await users_collection.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "account_status": "ativa",
                        "subscription": assinatura_do_usuario,
                        "updated_at": agora,
                    }
                },
            )
        else:
            usuarios = _ler_users_arquivo()
            for usuario in usuarios:
                if usuario.get("_id") == user_id:
                    usuario["account_status"] = "ativa"
                    usuario["subscription"] = assinatura_do_usuario
                    usuario["updated_at"] = agora
            _gravar_users_arquivo(usuarios)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"erro": str(exc)}, status_code=500)

    return {"assinatura": documento}


@app.post("/assinatura/plano")
async def trocar_plano(payload: TrocaPlanoRequest):
    """Troca o plano da assinatura ativa do usuário, mantendo o cartão vinculado."""
    user_id = payload.user_id.strip()
    plano = payload.plan_id.strip()
    if plano not in PRECO_PLANOS:
        return JSONResponse({"erro": "Plano inválido."}, status_code=400)

    usuario = await _buscar_usuario(user_id)
    resumo = (usuario or {}).get("subscription")
    if not usuario or usuario.get("account_status") != "ativa" or not resumo:
        return JSONResponse({"erro": "Nenhuma assinatura ativa para alterar."}, status_code=409)
    if resumo.get("plan_id") == plano:
        return JSONResponse({"erro": "Esse já é o seu plano atual."}, status_code=400)

    agora = agora_iso()
    novo_resumo = {
        **resumo,
        "plan_id": plano,
        "plan_name": NOME_PLANOS[plano],
        "monthly_amount": PRECO_PLATAFORMA + PRECO_PLANOS[plano],
    }
    try:
        if users_collection is not None:
            await users_collection.update_one(
                {"_id": user_id}, {"$set": {"subscription": novo_resumo, "updated_at": agora}}
            )
        else:
            usuarios = _ler_users_arquivo()
            for item in usuarios:
                if item.get("_id") == user_id:
                    item["subscription"] = novo_resumo
                    item["updated_at"] = agora
            _gravar_users_arquivo(usuarios)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"erro": str(exc)}, status_code=500)

    return {"usuario": usuario_publico({**usuario, "subscription": novo_resumo})}


@app.post("/conta/cancelar")
async def cancelar_conta(payload: CancelarContaRequest):
    """Marca account_active = false. O acesso segue até o fim do mês já pago."""
    user_id = payload.user_id.strip()
    if not user_id:
        return JSONResponse({"erro": "Usuário não encontrado."}, status_code=400)

    usuario = await _buscar_usuario(user_id)
    if not usuario:
        return JSONResponse({"erro": "Usuário não encontrado."}, status_code=404)
    if usuario.get("account_active") is False:
        return {"usuario": usuario_publico(usuario)}

    agora = agora_iso()
    try:
        if users_collection is not None:
            await users_collection.update_one(
                {"_id": user_id},
                {"$set": {"account_active": False, "updated_at": agora}},
            )
        else:
            usuarios = _ler_users_arquivo()
            for item in usuarios:
                if item.get("_id") == user_id:
                    item["account_active"] = False
                    item["updated_at"] = agora
            _gravar_users_arquivo(usuarios)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"erro": str(exc)}, status_code=500)

    usuario["account_active"] = False
    return {"usuario": usuario_publico(usuario)}


@app.get("/caso")
async def obter_caso(user_id: str = "", caso_id: str = ""):
    user_id = user_id.strip()
    caso_id = caso_id.strip()
    if not user_id or not caso_id:
        return JSONResponse({"erro": "Informe user_id e caso_id."}, status_code=400)
    if case_collection is None:
        return JSONResponse({"erro": "MongoDB não configurado."}, status_code=503)

    consulta_id = ObjectId(caso_id) if ObjectId.is_valid(caso_id) else caso_id
    # Aceita o _id do Mongo ou o caso_id da aplicação.
    documento = await case_collection.find_one(
        {"user_id": user_id, "$or": [{"_id": consulta_id}, {"caso_id": caso_id}]}
    )
    if not documento:
        return JSONResponse({"erro": "Caso não encontrado."}, status_code=404)

    documento["_id"] = str(documento["_id"])
    documento["transcript"] = _entradas_transcript(documento)
    return documento


async def _documentos_do_usuario(user_id: str) -> list[dict]:
    if case_collection is None:
        return [item for item in _ler_cases_arquivo() if item.get("user_id") == user_id]
    return await case_collection.find({"user_id": user_id}).to_list(length=1000)


async def _buscar_caso_do_usuario(user_id: str, caso_id: str) -> dict | None:
    if case_collection is None:
        return next(
            (item for item in _ler_cases_arquivo() if item.get("user_id") == user_id and _mesmo_caso(item, caso_id)),
            None,
        )
    consulta_id = ObjectId(caso_id) if ObjectId.is_valid(caso_id) else caso_id
    return await case_collection.find_one(
        {"user_id": user_id, "$or": [{"_id": consulta_id}, {"caso_id": caso_id}]}
    )


def _filtro_caso(user_id: str, caso_id: str) -> dict:
    consulta_id = ObjectId(caso_id) if ObjectId.is_valid(caso_id) else caso_id
    return {"user_id": user_id, "$or": [{"caso_id": caso_id}, {"_id": consulta_id}]}


@app.get("/casos")
async def listar_casos(user_id: str = ""):
    user_id = user_id.strip()
    if not user_id:
        return JSONResponse({"erro": "Informe o usuário."}, status_code=400)
    documentos = await _documentos_do_usuario(user_id)
    casos = [_caso_publico(item) for item in documentos if item.get("in_system") is not False]
    casos.sort(key=lambda item: item.get("updated_at") or "", reverse=True)
    return {"casos": casos}


@app.post("/casos")
async def criar_caso(payload: dict):
    user_id = (payload.get("user_id") or "").strip()
    caso_id = (payload.get("caso_id") or "").strip()
    title = (payload.get("title") or "").strip()
    client_name = (payload.get("client_name") or "").strip()
    legal_area = (payload.get("legal_area") or "").strip()
    if not user_id:
        return JSONResponse({"erro": "Informe o usuário."}, status_code=400)
    if not _caso_id_valido(caso_id):
        return JSONResponse({"erro": "Identificador do caso inválido."}, status_code=400)
    if not title or not client_name:
        return JSONResponse({"erro": "Informe o título e o cliente."}, status_code=400)
    if legal_area not in AREAS_JURIDICAS:
        return JSONResponse({"erro": "Escolha a área jurídica."}, status_code=400)
    if len(title) > 200 or len(client_name) > 200:
        return JSONResponse({"erro": "Título, cliente ou área longo demais."}, status_code=400)

    agora = agora_iso()
    campos = {
        "user_id": user_id,
        "caso_id": caso_id,
        "title": title,
        "client_name": client_name,
        "legal_area": legal_area,
        "in_system": True,
        "updated_at": agora,
    }
    if case_collection is None:
        lista = _ler_cases_arquivo()
        existente = next((item for item in lista if item.get("user_id") == user_id and _mesmo_caso(item, caso_id)), None)
        if existente:
            existente.update(campos)
        else:
            lista.append({
                **campos,
                "_id": caso_id,
                "status": "gravacao_pendente",
                "folder": "ativo",
                "documents": [],
                "transcript": [],
                "created_at": agora,
            })
        _gravar_cases_arquivo(lista)
        salvo = next(item for item in lista if item.get("user_id") == user_id and _mesmo_caso(item, caso_id))
        return {"caso": _caso_publico(salvo)}

    await case_collection.update_one(
        {"user_id": user_id, "caso_id": caso_id},
        {
            "$set": campos,
            "$setOnInsert": {
                "status": "gravacao_pendente",
                "folder": "ativo",
                "documents": [],
                "transcript": [],
                "created_at": agora,
            },
        },
        upsert=True,
    )
    salvo = await _buscar_caso_do_usuario(user_id, caso_id)
    return {"caso": _caso_publico(salvo or campos)}


@app.patch("/casos/{caso_id}")
async def atualizar_caso(caso_id: str, payload: dict):
    user_id = (payload.get("user_id") or "").strip()
    if not user_id:
        return JSONResponse({"erro": "Informe o usuário."}, status_code=400)
    campos: dict = {"updated_at": agora_iso()}
    if payload.get("folder") is not None:
        pasta = payload.get("folder")
        if pasta not in PASTAS_CASO:
            return JSONResponse({"erro": "Pasta inválida."}, status_code=400)
        campos["folder"] = pasta
    if payload.get("status") is not None:
        status = payload.get("status")
        if status not in STATUS_CASO:
            return JSONResponse({"erro": "Status inválido."}, status_code=400)
        campos["status"] = status
    if len(campos) == 1:
        return JSONResponse({"erro": "Nada para atualizar."}, status_code=400)

    if case_collection is None:
        lista = _ler_cases_arquivo()
        salvo = next((item for item in lista if item.get("user_id") == user_id and _mesmo_caso(item, caso_id)), None)
        if not salvo:
            return JSONResponse({"erro": "Caso não encontrado."}, status_code=404)
        salvo.update(campos)
        _gravar_cases_arquivo(lista)
        return {"caso": _caso_publico(salvo)}

    resultado = await case_collection.update_one(_filtro_caso(user_id, caso_id), {"$set": campos})
    if resultado.matched_count == 0:
        return JSONResponse({"erro": "Caso não encontrado."}, status_code=404)
    salvo = await _buscar_caso_do_usuario(user_id, caso_id)
    return {"caso": _caso_publico(salvo or {"caso_id": caso_id, **campos})}


@app.delete("/casos/{caso_id}")
async def excluir_caso(caso_id: str, user_id: str = ""):
    """Tira o caso da tela do cliente sem apagar o documento.

    ``in_system`` fica false. true significa que o caso ainda aparece para o usuário.
    """
    user_id = user_id.strip()
    if not user_id:
        return JSONResponse({"erro": "Informe o usuário."}, status_code=400)
    campos = {"in_system": False, "updated_at": agora_iso()}
    if case_collection is None:
        lista = _ler_cases_arquivo()
        salvo = next((item for item in lista if item.get("user_id") == user_id and _mesmo_caso(item, caso_id)), None)
        if not salvo:
            return JSONResponse({"erro": "Caso não encontrado."}, status_code=404)
        salvo.update(campos)
        _gravar_cases_arquivo(lista)
        return Response(status_code=204)

    resultado = await case_collection.update_one(_filtro_caso(user_id, caso_id), {"$set": campos})
    if resultado.matched_count == 0:
        return JSONResponse({"erro": "Caso não encontrado."}, status_code=404)
    return Response(status_code=204)


def _duracao_audio(valor) -> int | None:
    """Segundos do áudio enviado ou gravado. Ausente ou inválido não impede o salvamento."""
    if valor is None or isinstance(valor, bool):
        return None
    try:
        segundos = int(round(float(valor)))
    except (TypeError, ValueError):
        return None
    if segundos <= 0 or segundos > 360_000:
        return None
    return segundos


def _transcript(texto: str, momento: str, duracao_segundos: int | None, origem: str = "audio") -> dict:
    """Um item de `case.transcript`. `source`: "audio" (transcrição) ou "manual" (escrito à mão)."""
    entrada = {"id": str(uuid.uuid4()), "text": texto, "source": origem, "created_at": momento}
    if duracao_segundos is not None:
        entrada["duration_seconds"] = duracao_segundos
    return entrada


async def _anexar_transcript(filtro: dict, entrada: dict, momento: str) -> bool:
    """Acrescenta um item em `transcript` (o array só cresce). Devolve False se o caso não existe.

    Casos antigos têm `transcript` como objeto único (ou nulo): vira array antes do push.
    """
    atual = await case_collection.find_one(filtro, {"transcript": 1})
    if atual is None:
        return False
    bruto = atual.get("transcript")
    if not isinstance(bruto, list):
        legado = [bruto] if isinstance(bruto, dict) and str(bruto.get("text") or "").strip() else []
        await case_collection.update_one(
            {"$and": [filtro, {"transcript": {"$not": {"$type": "array"}}}]},
            {"$set": {"transcript": legado}},
        )
    await case_collection.update_one(
        filtro, {"$push": {"transcript": entrada}, "$set": {"updated_at": momento}}
    )
    return True


@app.post("/salvar-transcricao")
async def salvar_transcricao(payload: dict):
    """Acrescenta um relato em `transcript` do caso, na collection case.

    `transcript` é um array: cada item tem id, text, source ("audio" ou "manual", este para o
    relato escrito à mão), created_at e, no áudio, duration_seconds. Nada é gravado em outra
    collection; os documentos anexados ficam em `documents`.
    """
    texto = (payload.get("texto") or "").strip()
    user_id = (payload.get("user_id") or "").strip()
    caso_id = (payload.get("caso_id") or "").strip()
    origem = (payload.get("origem") or "audio").strip().lower()
    duracao_segundos = _duracao_audio(payload.get("duracao_segundos"))
    if not texto:
        return {"erro": "Texto vazio, nada para salvar."}
    if not user_id:
        return JSONResponse(
            {"erro": "Informe o usuário para vincular a transcrição."},
            status_code=400,
        )
    if origem not in ORIGENS_TRANSCRIPT:
        return JSONResponse({"erro": "Origem do relato inválida."}, status_code=400)
    if origem == "manual":
        duracao_segundos = None

    agora = time.strftime("%Y-%m-%d_%H-%M-%S")
    momento = agora_iso()
    pasta_txt = PASTA_BACK / "transcricoes"
    os.makedirs(pasta_txt, exist_ok=True)
    nome_arquivo_txt = str(pasta_txt / f"transcricao_{agora}.txt")
    with open(nome_arquivo_txt, "w", encoding="utf-8") as f:
        f.write(texto)

    resultado = {"arquivo_txt": nome_arquivo_txt}
    entrada = _transcript(texto, momento, duracao_segundos, origem)

    if case_collection is not None:
        try:
            if caso_id:
                # Único por (usuário, caso) só onde há caso_id: documentos antigos da
                # coleção não têm o campo e, como duplicados de caso_id nulo, faziam a
                # criação do índice — e com ela todo salvamento — falhar.
                await case_collection.create_index(
                    [("user_id", 1), ("caso_id", 1)],
                    unique=True,
                    partialFilterExpression={"caso_id": {"$type": "string"}},
                )
                filtro = {"user_id": user_id, "caso_id": caso_id}
                await case_collection.update_one(
                    filtro,
                    {
                        "$set": {"user_id": user_id, "caso_id": caso_id},
                        "$setOnInsert": {"created_at": momento, "documents": [], "transcript": []},
                    },
                    upsert=True,
                )
                await _anexar_transcript(filtro, entrada, momento)
                await case_collection.update_one(
                    {
                        "user_id": user_id,
                        "caso_id": caso_id,
                        "$or": [
                            {"status": {"$exists": False}},
                            {"status": None},
                            {"status": "gravacao_pendente"},
                        ],
                    },
                    {"$set": {"status": "em_analise"}},
                )
                salvo = await case_collection.find_one(filtro)
                resultado["case_id"] = str(salvo["_id"]) if salvo else caso_id
            else:
                caso = {
                    "user_id": user_id,
                    "transcript": [entrada],
                    "documents": [],
                    "created_at": momento,
                    "updated_at": momento,
                }
                insercao = await case_collection.insert_one(caso)
                resultado["case_id"] = str(insercao.inserted_id)
        except Exception as exc:  # noqa: BLE001
            resultado["erro_mongo"] = str(exc)
    else:
        resultado["aviso"] = "MONGODB_URI não configurada — salvo só localmente em .txt."

    return resultado


TIPOS_DOCUMENTO = {"pdf", "docx", "txt"}
MAX_DOCUMENTOS_CASO = 10
TAMANHO_MAX_DOCUMENTO = 15 * 1024 * 1024
# Assinatura dos arquivos: confere o conteúdo real, não só a extensão.
ASSINATURAS_DOCUMENTO = {"pdf": b"%PDF", "docx": b"PK"}


class _LimiteDocumentos(Exception):
    pass


def _anexar_documento_arquivo(user_id: str, caso_id: str, documento: dict, momento: str) -> bool:
    lista = _ler_cases_arquivo()
    caso = next((item for item in lista if item.get("user_id") == user_id and _mesmo_caso(item, caso_id)), None)
    if not caso:
        return False
    if len(caso.get("documents") or []) >= MAX_DOCUMENTOS_CASO:
        raise _LimiteDocumentos()
    caso.setdefault("documents", []).append(documento)
    caso["updated_at"] = momento
    if caso.get("status") in (None, "gravacao_pendente"):
        caso["status"] = "em_analise"
    _gravar_cases_arquivo(lista)
    return True


@app.post("/salvar-documento")
async def salvar_documento(payload: dict):
    """Anexa um texto já extraído (PDF, DOCX ou TXT) em documents do caso.

    Não grava em transcript: no repositório o arquivo fica na aba Documentos.
    """
    nome = (payload.get("nome") or "").strip()
    tipo = (payload.get("tipo") or "").strip().lower().lstrip(".")
    texto = (payload.get("texto") or "").strip()
    user_id = (payload.get("user_id") or "").strip()
    caso_id = (payload.get("caso_id") or "").strip()
    if not user_id or not _caso_id_valido(caso_id):
        return JSONResponse({"erro": "Informe o caso para anexar o documento."}, status_code=400)
    if tipo not in TIPOS_DOCUMENTO:
        return JSONResponse({"erro": "Envie um PDF, DOCX ou TXT."}, status_code=400)
    if len(texto) < 20:
        return JSONResponse({"erro": "Não foi possível ler texto suficiente neste arquivo."}, status_code=400)
    if len(texto) > 500_000 or len(nome) > 180:
        return JSONResponse({"erro": "O arquivo é grande demais para anexar."}, status_code=400)

    momento = agora_iso()
    documento = {
        "id": str(uuid.uuid4()),
        "name": nome or f"documento.{tipo}",
        "type": tipo,
        "text": texto,
        "created_at": momento,
    }
    try:
        if case_collection is not None:
            filtro = _filtro_caso(user_id, caso_id)
            # O limite entra no próprio filtro: o push só acontece se ainda há vaga (sem corrida).
            resultado = await case_collection.update_one(
                {"$and": [filtro, {f"documents.{MAX_DOCUMENTOS_CASO - 1}": {"$exists": False}}]},
                {"$push": {"documents": documento}, "$set": {"updated_at": momento}},
            )
            if resultado.matched_count == 0:
                if await case_collection.find_one(filtro, {"_id": 1}):
                    return JSONResponse(
                        {"erro": f"Limite de {MAX_DOCUMENTOS_CASO} documentos por caso atingido."},
                        status_code=409,
                    )
                return JSONResponse({"erro": "Caso não encontrado."}, status_code=404)
            await case_collection.update_one(
                {
                    "$and": [
                        _filtro_caso(user_id, caso_id),
                        {
                            "$or": [
                                {"status": {"$exists": False}},
                                {"status": None},
                                {"status": "gravacao_pendente"},
                            ]
                        },
                    ]
                },
                {"$set": {"status": "em_analise"}},
            )
        elif not _anexar_documento_arquivo(user_id, caso_id, documento, momento):
            return JSONResponse({"erro": "Caso não encontrado."}, status_code=404)
    except _LimiteDocumentos:
        return JSONResponse(
            {"erro": f"Limite de {MAX_DOCUMENTOS_CASO} documentos por caso atingido."}, status_code=409
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"erro": str(exc)}, status_code=500)
    return {"documento": {"id": documento["id"], "name": documento["name"], "type": documento["type"]}}


@app.post("/anexar-documento")
async def anexar_documento(
    user_id: str = Form(""),
    caso_id: str = Form(""),
    arquivo: UploadFile = File(...),
):
    """Recebe PDF, DOCX ou TXT, extrai só o texto aqui no servidor e anexa em documents do caso."""
    nome = (arquivo.filename or "").strip()
    tipo = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
    if tipo not in TIPOS_DOCUMENTO:
        return JSONResponse({"erro": "Envie um PDF, DOCX ou TXT."}, status_code=415)

    conteudo = await arquivo.read(TAMANHO_MAX_DOCUMENTO + 1)
    if len(conteudo) > TAMANHO_MAX_DOCUMENTO:
        return JSONResponse({"erro": "O arquivo passa de 15 MB."}, status_code=413)
    assinatura = ASSINATURAS_DOCUMENTO.get(tipo)
    if assinatura and not conteudo.startswith(assinatura):
        return JSONResponse({"erro": f"O arquivo não parece ser um {tipo.upper()} válido."}, status_code=400)

    try:
        extraido = await asyncio.to_thread(extract_text, nome, conteudo)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"erro": f"Não foi possível ler o arquivo: {exc}"}, status_code=422)
    if len(extraido.text) < 20:
        return JSONResponse(
            {"erro": "Não encontrei texto neste arquivo. Se for um PDF escaneado (imagem), ele precisa de OCR antes."},
            status_code=422,
        )

    resposta = await salvar_documento(
        {"user_id": user_id, "caso_id": caso_id, "nome": nome, "tipo": tipo, "texto": extraido.text}
    )
    if isinstance(resposta, JSONResponse):
        return resposta
    return {**resposta, "texto": extraido.text}


# ---------------------------------------------------------------------------
# Análise preliminar, chat e minutas (módulo `analise`)
# ---------------------------------------------------------------------------


async def contexto_do_caso(user_id: str, caso_id: str) -> dict | None:
    """Dados do caso para a IA. None = caso inexistente, de outro usuário ou excluído."""
    documento = await _buscar_caso_do_usuario(user_id, caso_id)
    if not documento or documento.get("in_system") is False:
        return None
    # Os relatos vêm só do próprio caso: cada item de `transcript`, em ordem cronológica.
    relatos = [
        {"texto": item["text"], "criado_em": item.get("created_at"), "origem": item.get("source")}
        for item in _entradas_transcript(documento)
    ]
    return {
        "titulo": documento.get("title") or "",
        "cliente": documento.get("client_name") or "",
        "area": documento.get("legal_area") or None,
        "relatos": relatos,
        "documentos": [d for d in documento.get("documents") or [] if isinstance(d, dict)],
    }


async def marcar_caso_analisado(user_id: str, caso_id: str, versao: int) -> None:
    if case_collection is None:
        return
    filtro = _filtro_caso(user_id, caso_id)
    await case_collection.update_one(filtro, {"$set": {"analysis_version": versao, "updated_at": agora_iso()}})
    await case_collection.update_one(
        {"$and": [filtro, {"status": {"$in": [None, "gravacao_pendente"]}}]},
        {"$set": {"status": "em_analise"}},
    )


app.include_router(criar_router_analise(contexto_do_caso, lambda: armazenamento_ia, marcar_caso_analisado))


@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            if not audio_bytes:
                continue
            try:
                texto = await asyncio.to_thread(transcrever_bloco, audio_bytes)
            except Exception as exc:  # noqa: BLE001
                await websocket.send_json(
                    {"type": "error", "message": f"Falha ao transcrever: {exc}"}
                )
                continue
            if texto:
                await websocket.send_json(
                    {"type": "transcript", "text": texto, "is_final": True}
                )
    except WebSocketDisconnect:
        pass
