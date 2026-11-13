"""
Camada agnóstica de provedor de IA (BYOK). A chave nunca é logada nem persistida aqui.
Nomes de modelo padrão são configuração: sobrescreva por variável de ambiente
(SOPHIA_MODEL_OPENAI, SOPHIA_MODEL_ANTHROPIC, SOPHIA_MODEL_GOOGLE, SOPHIA_MODEL_GROQ),
pois os provedores descontinuam modelos com frequência.
"""
from __future__ import annotations

import json
import os
import re
import time
from abc import ABC, abstractmethod
from typing import Iterator

from .busca_web import dominios_da_busca


class LLMError(RuntimeError):
    """Erro de comunicação com o provedor de IA escolhido pelo usuário."""


def busca_web_ligada() -> bool:
    """Busca na web das IAs que a suportam. Desligada por padrão: na OpenAI é cobrada à parte."""
    return (os.environ.get("SOPHIA_BUSCA_WEB") or "").strip().lower() in {"1", "true", "sim", "on"}


def _consumo_vazio() -> dict:
    return {"chamadas": 0, "entrada": 0, "entrada_cache": 0, "saida": 0, "raciocinio": 0, "buscas": 0}


def _campo(obj, nome, padrao=None):
    """Lê atributo de objeto do SDK ou chave de dict."""
    if isinstance(obj, dict):
        return obj.get(nome, padrao)
    return getattr(obj, nome, padrao)


class BaseLLMProvider(ABC):
    name: str
    env_var: str
    fallback_model: str

    def __init__(self, api_key: str, model: str | None = None):
        if not api_key:
            raise LLMError("Chave de API não informada para este provedor.")
        self.api_key = api_key
        self.model = model or os.environ.get(self.env_var) or self.fallback_model
        self.consumo = _consumo_vazio()
        # URLs que a busca na web devolveu na última chamada (fontes consultadas e citações).
        self.fontes_web: list = []

    def _somar_uso(self, entrada=0, entrada_cache=0, saida=0, raciocinio=0, buscas=0) -> None:
        """Tokens de uma chamada, informados pelo provedor. Somam até `tirar_consumo()`."""
        self.consumo["chamadas"] += 1
        self.consumo["entrada"] += int(entrada or 0)
        self.consumo["entrada_cache"] += int(entrada_cache or 0)
        self.consumo["saida"] += int(saida or 0)
        self.consumo["raciocinio"] += int(raciocinio or 0)
        self.consumo["buscas"] += int(buscas or 0)

    def busca_ativa(self, use_web_search: bool = True) -> bool:
        """Se esta chamada vai pesquisar na web com a lista de sites (hoje só a OpenAI)."""
        return False

    def tirar_consumo(self) -> dict:
        """Devolve os tokens gastos desde a última leitura e zera o contador."""
        atual, self.consumo = self.consumo, _consumo_vazio()
        return atual

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str,
                 use_web_search: bool = True, json_mode: bool = False) -> str:
        """Retorna texto. json_mode=True só na análise inicial (resposta JSON)."""

    def generate_stream(self, system_prompt: str, user_prompt: str,
                        use_web_search: bool = True) -> Iterator[str]:
        """
        Texto em trechos, conforme a IA escreve (chat). Provedor sem streaming aqui entrega a
        resposta inteira num trecho só; quem consome não precisa saber a diferença.
        """
        yield self.generate(system_prompt, user_prompt, use_web_search=use_web_search, json_mode=False)


class OpenAIProvider(BaseLLMProvider):
    name = "openai"
    env_var = "SOPHIA_MODEL_OPENAI"
    fallback_model = "gpt-4.1"

    def _cliente(self):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise LLMError("Pacote 'openai' não instalado (pip install openai).") from e
        return OpenAI(api_key=self.api_key)

    def generate(self, system_prompt, user_prompt, use_web_search=True, json_mode=False):
        client = self._cliente()
        kwargs = self._parametros(system_prompt, user_prompt, use_web_search, json_mode)
        self.fontes_web = []
        try:
            resp = client.responses.create(**kwargs)
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"Falha ao chamar a OpenAI: {e}") from e
        self._registrar_resposta(resp)
        return resp.output_text or ""

    def generate_stream(self, system_prompt, user_prompt, use_web_search=True):
        client = self._cliente()
        kwargs = self._parametros(system_prompt, user_prompt, use_web_search, False)
        self.fontes_web = []
        try:
            for evento in client.responses.create(**kwargs, stream=True):
                tipo = _campo(evento, "type")
                if tipo == "response.output_text.delta":
                    trecho = _campo(evento, "delta") or ""
                    if trecho:
                        yield trecho
                elif tipo in ("response.completed", "response.incomplete"):
                    self._registrar_resposta(_campo(evento, "response"))
                elif tipo == "response.failed":
                    falha = _campo(_campo(evento, "response"), "error")
                    raise LLMError(f"Falha ao chamar a OpenAI: {_campo(falha, 'message') or 'resposta interrompida'}")
                elif tipo == "error":
                    raise LLMError(f"Falha ao chamar a OpenAI: {_campo(evento, 'message') or 'erro no stream'}")
        except LLMError:
            raise
        except Exception as e:  # noqa: BLE001
            raise LLMError(f"Falha ao chamar a OpenAI: {e}") from e

    def _registrar_resposta(self, resp) -> None:
        """Tokens gastos e páginas consultadas de uma resposta completa."""
        if resp is None:
            return
        uso = _campo(resp, "usage")
        if uso is not None:
            entrada_det = _campo(uso, "input_tokens_details")
            saida_det = _campo(uso, "output_tokens_details")
            self._somar_uso(
                entrada=_campo(uso, "input_tokens", 0),
                entrada_cache=_campo(entrada_det, "cached_tokens", 0) if entrada_det else 0,
                saida=_campo(uso, "output_tokens", 0),
                raciocinio=_campo(saida_det, "reasoning_tokens", 0) if saida_det else 0,
                buscas=sum(1 for item in (_campo(resp, "output") or [])
                           if _campo(item, "type") == "web_search_call"),
            )
        self.fontes_web = _urls_da_resposta(resp)

    def _parametros(self, system_prompt, user_prompt, use_web_search, json_mode) -> dict:
        kwargs = dict(model=self.model, instructions=system_prompt, input=user_prompt)
        if self.busca_ativa(use_web_search):
            kwargs["tools"] = [{
                "type": "web_search",
                # Só sites jurídicos (busca_web.DOMINIOS); subdomínios entram junto.
                "filters": {"allowed_domains": dominios_da_busca()},
                "user_location": {"type": "approximate", "country": "BR"},
            }]
            # Lista completa das páginas consultadas, para validar os links dos cards.
            kwargs["include"] = ["web_search_call.action.sources"]
        elif json_mode:
            # Análise: a OpenAI garante JSON válido (o prompt de sistema já pede JSON).
            kwargs["text"] = {"format": {"type": "json_object"}}
        esforco = (os.environ.get("SOPHIA_RACIOCINIO_OPENAI") or "").strip().lower()
        if esforco:
            # Modelos de raciocínio (ex.: gpt-6-luna): none, low, medium, high...
            kwargs["reasoning"] = {"effort": esforco}
        return kwargs

    def busca_ativa(self, use_web_search: bool = True) -> bool:
        return bool(use_web_search) and busca_web_ligada()


def _urls_da_resposta(resp) -> list:
    """URLs das páginas consultadas pela busca e das citações (url_citation) da resposta."""
    urls = []
    for item in _campo(resp, "output") or []:
        tipo = _campo(item, "type")
        if tipo == "web_search_call":
            acao = _campo(item, "action")
            for fonte in _campo(acao, "sources") or []:
                if _campo(fonte, "url"):
                    urls.append(_campo(fonte, "url"))
            if _campo(acao, "url"):  # open_page / find_in_page
                urls.append(_campo(acao, "url"))
        elif tipo == "message":
            for parte in _campo(item, "content") or []:
                for nota in _campo(parte, "annotations") or []:
                    if _campo(nota, "type") == "url_citation" and _campo(nota, "url"):
                        urls.append(_campo(nota, "url"))
    return list(dict.fromkeys(urls))


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
            dados = r.json()
            self._somar_uso_groq(dados.get("usage") or {})
            return dados["choices"][0]["message"]["content"] or ""
        raise LLMError("A IA não respondeu. Tente de novo.")

    def generate_stream(self, system_prompt, user_prompt, use_web_search=True):
        import httpx

        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": user_prompt}],
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        for tentativa in range(self.TENTATIVAS_LIMITE):
            try:
                with httpx.stream("POST", self.URL, json=body, timeout=120.0,
                                  headers={"Authorization": f"Bearer {self.api_key}"}) as r:
                    if r.status_code != 200:
                        r.read()
                        if r.status_code == 429 and tentativa < self.TENTATIVAS_LIMITE - 1:
                            # O limite chega antes do primeiro trecho: dá para esperar e repetir.
                            time.sleep(self._espera(r))
                            continue
                        if r.status_code == 429:
                            raise LLMError("A IA atingiu o limite de uso por minuto. "
                                           "Aguarde alguns segundos e tente de novo.")
                        raise LLMError(f"Groq retornou status {r.status_code}: {r.text[:300]}")
                    for linha in r.iter_lines():
                        if not linha.startswith("data:"):
                            continue
                        dado = linha[5:].strip()
                        if dado == "[DONE]":
                            break
                        pedaco = json.loads(dado)
                        self._somar_uso_groq(pedaco.get("usage") or (pedaco.get("x_groq") or {}).get("usage"))
                        for escolha in pedaco.get("choices") or []:
                            trecho = (escolha.get("delta") or {}).get("content")
                            if trecho:
                                yield trecho
                    return
            except httpx.HTTPError as e:
                raise LLMError(f"Falha ao chamar o Groq: {e}") from e
        raise LLMError("A IA não respondeu. Tente de novo.")

    def _somar_uso_groq(self, uso) -> None:
        """Uso de uma chamada. No stream só o último pedaço traz o uso; os demais vêm sem (None)."""
        if uso is None:
            return
        self._somar_uso(
            entrada=uso.get("prompt_tokens", 0),
            entrada_cache=(uso.get("prompt_tokens_details") or {}).get("cached_tokens", 0),
            saida=uso.get("completion_tokens", 0),
            raciocinio=(uso.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
        )

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


def nome_do_provedor() -> str:
    return (os.environ.get("SOPHIA_LLM_PROVIDER") or "groq").strip().lower()


def descricao_da_ia() -> dict:
    """Provedor e modelo ativos, para o /health. Nunca inclui a chave."""
    nome = nome_do_provedor()
    cls = PROVIDERS.get(nome)
    if cls is None:
        return {"provedor": nome, "erro": "SOPHIA_LLM_PROVIDER inválido"}
    return {
        "provedor": nome,
        "modelo": os.environ.get(cls.env_var) or cls.fallback_model,
        "chave": "configurada" if (os.environ.get(_ENV_CHAVE[nome]) or "").strip() else "ausente",
        "busca_web": busca_web_ligada(),
        "sites_da_busca": len(dominios_da_busca()) if nome == "openai" and busca_web_ligada() else None,
        "raciocinio": (os.environ.get("SOPHIA_RACIOCINIO_OPENAI") or "padrão do modelo")
        if nome == "openai" else None,
    }


def provider_do_servidor() -> BaseLLMProvider:
    """
    Provedor configurado no servidor (créditos de IA vêm da assinatura, não do usuário).
    SOPHIA_LLM_PROVIDER escolhe o provedor (padrão: groq) e a chave vem de <PROVEDOR>_API_KEY
    no .env do backend. A chave nunca passa pelo navegador.
    """
    nome = nome_do_provedor()
    if nome not in PROVIDERS:
        raise LLMError(f"SOPHIA_LLM_PROVIDER inválido: '{nome}'. Opções: {', '.join(PROVIDERS)}")
    chave = (os.environ.get(_ENV_CHAVE[nome]) or "").strip()
    if not chave:
        raise LLMError(f"Serviço de IA não configurado: defina {_ENV_CHAVE[nome]} em backend/.env.")
    return get_provider(nome, chave)
