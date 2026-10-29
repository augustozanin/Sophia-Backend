"""
Persistência no MongoDB (banco `sophia-data`) da análise, do chat e das minutas.

Cada coisa tem sua coleção e cada registro é um documento próprio, inserido sem reescrever
o caso. Assim o documento do caso continua pequeno, nada se perde quando algo novo chega e
nenhuma requisição precisa mandar o histórico inteiro:

- `analises`: uma versão da análise por documento (JSON validado da IA). Os cards são
  derivados na leitura pelo `mapeador`, então mudar a forma de exibir não exige migração.
- `mensagens`: uma mensagem do chat por documento, só acrescentada.
- `pecas`: uma minuta gerada por documento.

Os relatos (transcrições de áudio e textos escritos à mão) e os documentos anexados não têm
collection própria: ficam no próprio caso, em `case.transcript` e `case.documents`.

Toda leitura e escrita filtra por (user_id, caso_id): o isolamento por usuário vale aqui.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

_FUSO = timezone(timedelta(hours=-3))


def agora() -> str:
    return datetime.now(_FUSO).strftime("%Y-%m-%dT%H:%M:%S")


def _sem_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in doc.items() if k != "_id"}


class Armazenamento:
    def __init__(self, db) -> None:
        self.analises = db["analises"]
        self.mensagens = db["mensagens"]
        self.pecas = db["pecas"]
        self._indices_prontos = False

    async def garantir_indices(self) -> None:
        if self._indices_prontos:
            return
        await self.analises.create_index(
            [("user_id", ASCENDING), ("caso_id", ASCENDING), ("versao", DESCENDING)], unique=True)
        await self.mensagens.create_index(
            [("user_id", ASCENDING), ("caso_id", ASCENDING), ("criada_em", ASCENDING), ("_id", ASCENDING)])
        await self.pecas.create_index(
            [("user_id", ASCENDING), ("caso_id", ASCENDING), ("gerada_em", DESCENDING)])
        self._indices_prontos = True

    # ------------------------------------------------------------ análises
    async def salvar_analise(self, user_id: str, caso_id: str, analise: Dict[str, Any],
                             documentos_meta: List[Dict[str, Any]], modelo: str,
                             origem: str = "relato", mensagens_consideradas: int = 0) -> Dict[str, Any]:
        await self.garantir_indices()
        for _ in range(3):  # duas análises simultâneas disputam a mesma versão
            ultima = await self.ultima_analise(user_id, caso_id)
            registro = {
                "user_id": user_id, "caso_id": caso_id,
                "versao": (ultima["versao"] if ultima else 0) + 1,
                "gerada_em": agora(), "modelo": modelo,
                "analise": analise, "documentos_meta": documentos_meta,
                # "chat" = versão que incorporou as mensagens do advogado no chat.
                "origem": origem, "mensagens_consideradas": mensagens_consideradas,
            }
            try:
                await self.analises.insert_one(registro)
                return _sem_id(registro)
            except DuplicateKeyError:
                continue
        raise RuntimeError("Não foi possível salvar a análise. Tente de novo.")

    async def listar_analises(self, user_id: str, caso_id: str) -> List[Dict[str, Any]]:
        """Mais recente primeiro."""
        cursor = self.analises.find({"user_id": user_id, "caso_id": caso_id}).sort("versao", DESCENDING)
        return [_sem_id(d) for d in await cursor.to_list(length=200)]

    async def ultima_analise(self, user_id: str, caso_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.analises.find_one({"user_id": user_id, "caso_id": caso_id},
                                           sort=[("versao", DESCENDING)])
        return _sem_id(doc) if doc else None

    # ------------------------------------------------------------ chat
    @staticmethod
    def _mensagem(doc: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": str(doc["_id"]), "papel": doc["papel"], "conteudo": doc["conteudo"],
                "criada_em": doc["criada_em"]}

    async def listar_mensagens(self, user_id: str, caso_id: str, limite: int = 200) -> List[Dict[str, Any]]:
        """As `limite` mais recentes, em ordem cronológica."""
        cursor = (self.mensagens.find({"user_id": user_id, "caso_id": caso_id})
                  .sort([("criada_em", DESCENDING), ("_id", DESCENDING)]).limit(limite))
        docs = await cursor.to_list(length=limite)
        return [self._mensagem(d) for d in reversed(docs)]

    async def adicionar_mensagens(self, user_id: str, caso_id: str,
                                  itens: Iterable[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """itens: [(papel, conteudo)], papel "user" ou "assistant". Devolve só as novas."""
        await self.garantir_indices()
        momento = agora()
        docs = [{"_id": ObjectId(), "user_id": user_id, "caso_id": caso_id, "papel": papel,
                 "conteudo": conteudo, "criada_em": momento} for papel, conteudo in itens]
        if docs:
            await self.mensagens.insert_many(docs)
        return [self._mensagem(d) for d in docs]

    # ------------------------------------------------------------ peças
    @staticmethod
    def _peca(doc: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": str(doc["_id"]), **{k: v for k, v in doc.items() if k not in ("_id", "user_id")}}

    async def salvar_peca(self, user_id: str, caso_id: str, modelo: Dict[str, Any], texto: str,
                          instrucoes: Optional[str], analise_versao: Optional[int]) -> Dict[str, Any]:
        await self.garantir_indices()
        doc = {"_id": ObjectId(), "user_id": user_id, "caso_id": caso_id, "modelo_id": modelo["id"],
               "titulo": modelo["nome"], "texto": texto, "instrucoes": instrucoes or None,
               "analise_versao": analise_versao, "gerada_em": agora()}
        await self.pecas.insert_one(doc)
        return self._peca(doc)

    async def listar_pecas(self, user_id: str, caso_id: str) -> List[Dict[str, Any]]:
        cursor = (self.pecas.find({"user_id": user_id, "caso_id": caso_id}, {"texto": 0})
                  .sort("gerada_em", DESCENDING))
        return [self._peca(d) for d in await cursor.to_list(length=200)]

    async def obter_peca(self, user_id: str, caso_id: str, peca_id: str) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(peca_id):
            return None
        doc = await self.pecas.find_one({"_id": ObjectId(peca_id), "user_id": user_id, "caso_id": caso_id})
        return self._peca(doc) if doc else None
