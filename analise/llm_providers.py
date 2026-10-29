"""
Camada agnóstica de provedor de IA (BYOK). A chave nunca é logada nem persistida aqui.
Nomes de modelo padrão são configuração: sobrescreva por variável de ambiente
(SOPHIA_MODEL_OPENAI, SOPHIA_MODEL_ANTHROPIC, SOPHIA_MODEL_GOOGLE, SOPHIA_MODEL_GROQ),
pois os provedores descontinuam modelos com frequência.
"""
from __future__ import annotations

import os
import re
import time
from abc import ABC, abstractmethod


class LLMError(RuntimeError):
    """Erro de comunicação com o provedor de IA escolhido pelo usuário."""


class BaseLLMProvider(ABC):
    name: str
    env_var: str
    fallback_model: str

    def __init__(self, api_key: str, model: str | None = None):
        if not api_key:
            raise LLMError("Chave de API não informada para este provedor.")
        self.api_key = api_key
        self.model = model or os.environ.get(self.env_var) or self.fallback_model

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str,
                 use_web_search: bool = True, json_mode: bool = False) -> str:
        """Retorna texto. json_mode=True só na análise inicial (resposta JSON)."""


class OpenAIProvider(BaseLLMProvider):
    name = "openai"
    env_var = "SOPHIA_MODEL_OPENAI"
    fallback_model = "gpt-4.1"

    def generate(self, system_prompt, user_prompt, use_web_search=True, json_mode=False):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise LLMError("Pacote 'openai' não instalado (pip install openai).") from e
        client = OpenAI(api_key=self.api_key)
        tools = [{"type": "web_search_preview"}] if use_web_search else None
        try:
            resp = client.responses.create(
                model=self.model, instructions=system_prompt,
                input=user_prompt, tools=tools,
            )
            return resp.output_text
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"Falha ao chamar a OpenAI: {e}") from e


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"
    env_var = "SOPHIA_MODEL_ANTHROPIC"
    fallback_model = "claude-sonnet-4-6"

    def generate(self, system_prompt, user_prompt, use_web_search=True, json_mode=False):
        try:
            import anthropic
        except ImportError as e:
            raise LLMError("Pacote 'anthropic' não instalado (pip install anthropic).") from e
        client = anthropic.Anthropic(api_key=self.api_key)
        tools = [{"type": "web_search_20250305", "name": "web_search"}] if use_web_search else None
        try:
            kwargs = dict(
                model=self.model, max_tokens=8000, system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            if tools:
                kwargs["tools"] = tools
            resp = client.messages.create(**kwargs)
            return "\n".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"Falha ao chamar a Anthropic: {e}") from e


class GoogleProvider(BaseLLMProvider):
    name = "google"
    env_var = "SOPHIA_MODEL_GOOGLE"
    fallback_model = "gemini-3.5-flash"

    def generate(self, system_prompt, user_prompt, use_web_search=True, json_mode=False):
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise LLMError("Pacote 'google-genai' não instalado (pip install google-genai).") from e
        client = genai.Client(api_key=self.api_key)
        tools = [types.Tool(google_search=types.GoogleSearch())] if use_web_search else None
        try:
            resp = client.models.generate_content(
                model=self.model, contents=user_prompt,
                config=types.GenerateContentConfig(system_instruction=system_prompt, tools=tools),
            )
            return resp.text or ""
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"Falha ao chamar o Google Gemini: {e}") from e


class GroqProvider(BaseLLMProvider):
    name = "groq"
    env_var = "SOPHIA_MODEL_GROQ"
    # Mesmo modelo que o backend já usa em /revisar-transcricao. Verifique na Groq: modelos mudam.
    fallback_model = "openai/gpt-oss-120b"
    URL = "https://api.groq.com/openai/v1/chat/completions"

    def generate(self, system_prompt, user_prompt, use_web_search=True, json_mode=False):
        import httpx  # já é dependência do backend

        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": user_prompt}],
        }
        # response_format SÓ na análise inicial: forçá-lo em chat/peça quebra essas rotas.
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        for tentativa in range(self.TENTATIVAS_LIMITE):
            try:
                r = httpx.post(self.URL, json=body, timeout=120.0,
                               headers={"Authorization": f"Bearer {self.api_key}"})
            except httpx.HTTPError as e:
                raise LLMError(f"Falha ao chamar o Groq: {e}") from e
            if r.status_code == 429 and tentativa < self.TENTATIVAS_LIMITE - 1:
                # Limite de tokens por minuto: espera o que o Groq pede e tenta de novo.
                time.sleep(self._espera(r))
                continue
            if r.status_code == 429:
                raise LLMError("A IA atingiu o limite de uso por minuto. Aguarde alguns segundos e tente de novo.")
            if r.status_code != 200:
                raise LLMError(f"Groq retornou status {r.status_code}: {r.text[:300]}")
            return r.json()["choices"][0]["message"]["content"] or ""
        raise LLMError("A IA não respondeu. Tente de novo.")

    TENTATIVAS_LIMITE = 3
    ESPERA_MAXIMA = 20.0

    @classmethod
    def _espera(cls, r) -> float:
        """Segundos sugeridos no header `retry-after` ou no texto ("try again in 5.57s")."""
        try:
            return min(float(r.headers.get("retry-after", "")) + 0.5, cls.ESPERA_MAXIMA)
        except ValueError:
            pass
        achado = re.search(r"try again in ([\d.]+)s", r.text)
        return min(float(achado.group(1)) + 0.5, cls.ESPERA_MAXIMA) if achado else 5.0


PROVIDERS = {c.name: c for c in (OpenAIProvider, AnthropicProvider, GoogleProvider, GroqProvider)}


def get_provider(name: str, api_key: str, model: str | None = None) -> BaseLLMProvider:
    cls = PROVIDERS.get(name)
    if cls is None:
        raise LLMError(f"Provedor '{name}' não suportado. Opções: {', '.join(PROVIDERS)}")
    return cls(api_key=api_key, model=model)


_ENV_CHAVE = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
              "google": "GOOGLE_API_KEY", "groq": "GROQ_API_KEY"}


def provider_do_servidor() -> BaseLLMProvider:
    """
    Provedor configurado no servidor (créditos de IA vêm da assinatura, não do usuário).
    SOPHIA_LLM_PROVIDER escolhe o provedor (padrão: groq) e a chave vem de <PROVEDOR>_API_KEY
    no .env do backend. A chave nunca passa pelo navegador.
    """
    nome = (os.environ.get("SOPHIA_LLM_PROVIDER") or "groq").strip().lower()
    if nome not in PROVIDERS:
        raise LLMError(f"SOPHIA_LLM_PROVIDER inválido: '{nome}'. Opções: {', '.join(PROVIDERS)}")
    chave = (os.environ.get(_ENV_CHAVE[nome]) or "").strip()
    if not chave:
        raise LLMError(f"Serviço de IA não configurado: defina {_ENV_CHAVE[nome]} em backend/.env.")
    return get_provider(nome, chave)
