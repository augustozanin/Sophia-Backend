"""
Persistência do acompanhamento de prazos no MongoDB (banco `sophia-data`).

- `monitoramentos`: o que o advogado pediu para acompanhar. Um documento por OAB
  (`tipo: "oab"`) ou por processo (`tipo: "processo"`). `caso_id` é opcional: liga o
  processo a um caso da Sophia, sem obrigar caso nenhum a ter processo.
- `publicacoes`: uma intimação do DJEN por documento, única por (user_id, djen_id).
  `monitoramento_ids` diz por quais monitoramentos ela chegou (a mesma intimação pode vir
  pela OAB e pelo número do processo). `situacao`: "pendente" (ninguém tratou ainda),
  "agendada" (virou prazo) ou "sem_prazo" (o advogado marcou que não exige providência).
- `prazos`: o prazo que o advogado definiu, com a data final escolhida por ele.

Toda leitura e escrita filtra por user_id.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

LIMITE_PUBLICACOES = 300


def oid(valor: str) -> Optional[ObjectId]:
    return ObjectId(valor) if ObjectId.is_valid(str(valor or "")) else None


class ArmazenamentoPrazos:
    def __init__(self, db) -> None:
        self.monitoramentos = db["monitoramentos"]
        self.publicacoes = db["publicacoes"]
        self.prazos = db["prazos"]
        self._indices_prontos = False

    async def garantir_indices(self) -> None:
        if self._indices_prontos:
            return
        await self.monitoramentos.create_index([("user_id", ASCENDING), ("chave", ASCENDING)], unique=True)
        await self.publicacoes.create_index([("user_id", ASCENDING), ("djen_id", ASCENDING)], unique=True)
        await self.publicacoes.create_index(
            [("user_id", ASCENDING), ("numero_processo", ASCENDING), ("data_disponibilizacao", DESCENDING)])
        await self.prazos.create_index([("user_id", ASCENDING), ("data_final", ASCENDING)])
        self._indices_prontos = True

    # ------------------------------------------------------------ monitoramentos
    async def listar_monitoramentos(self, user_id: str, caso_id: Optional[str] = None) -> List[Dict[str, Any]]:
        filtro: Dict[str, Any] = {"user_id": user_id}
        if caso_id:
            filtro["caso_id"] = caso_id
        return await self.monitoramentos.find(filtro).sort("criado_em", ASCENDING).to_list(length=200)

    async def obter_monitoramento(self, user_id: str, monitoramento_id: str) -> Optional[Dict[str, Any]]:
        chave = oid(monitoramento_id)
        if not chave:
            return None
        return await self.monitoramentos.find_one({"_id": chave, "user_id": user_id})

    async def monitoramento_por_chave(self, user_id: str, chave: str) -> Optional[Dict[str, Any]]:
        return await self.monitoramentos.find_one({"user_id": user_id, "chave": chave})

    async def contar_monitoramentos(self, user_id: str) -> int:
        return len(await self.listar_monitoramentos(user_id))

    async def criar_monitoramento(self, documento: Dict[str, Any]) -> Dict[str, Any]:
        await self.garantir_indices()
        documento = {"_id": ObjectId(), **documento}
        await self.monitoramentos.insert_one(documento)
        return documento

    async def atualizar_monitoramento(self, user_id: str, monitoramento_id: ObjectId, campos: Dict[str, Any]) -> None:
        await self.monitoramentos.update_one({"_id": monitoramento_id, "user_id": user_id}, {"$set": campos})

    async def remover_monitoramento(self, user_id: str, monitoramento_id: ObjectId) -> None:
        """Some o monitoramento e as intimações que só ele trouxe e ninguém tratou.
        Intimação que virou prazo fica, para o prazo não perder a origem."""
        await self.monitoramentos.delete_one({"_id": monitoramento_id, "user_id": user_id})
        texto_id = str(monitoramento_id)
        await self.publicacoes.update_many({"user_id": user_id, "monitoramento_ids": texto_id},
                                           {"$pull": {"monitoramento_ids": texto_id}})
        await self.publicacoes.delete_many({"user_id": user_id, "monitoramento_ids": {"$size": 0},
                                            "situacao": {"$ne": "agendada"}})

    async def processo_vinculado(self, user_id: str, numero_processo: str) -> Optional[Dict[str, Any]]:
        """Monitoramento do processo, se houver (com o caso a que ele está ligado)."""
        return await self.monitoramento_por_chave(user_id, f"processo:{numero_processo}")

    # ------------------------------------------------------------ publicações
    async def salvar_publicacoes(self, user_id: str, monitoramento_id: str, itens: Iterable[Dict[str, Any]],
                                 momento: str) -> int:
        """Grava as intimações novas e acrescenta o monitoramento nas que já existiam. Devolve quantas são novas."""
        await self.garantir_indices()
        novas = 0
        for item in itens:
            fixos = {k: v for k, v in item.items() if k not in ("cancelada", "motivo_cancelamento")}
            resultado = await self.publicacoes.update_one(
                {"user_id": user_id, "djen_id": item["djen_id"]},
                {
                    "$setOnInsert": {**fixos, "user_id": user_id, "situacao": "pendente", "capturada_em": momento},
                    # Cancelamento pode chegar depois: sempre vale o que o DJEN diz agora.
                    "$set": {"cancelada": item.get("cancelada", False),
                             "motivo_cancelamento": item.get("motivo_cancelamento")},
                    "$addToSet": {"monitoramento_ids": monitoramento_id},
                },
                upsert=True,
            )
            if getattr(resultado, "upserted_id", None) is not None:
                novas += 1
        return novas

    async def listar_publicacoes(self, user_id: str, processos: Optional[List[str]], desde: str) -> List[Dict[str, Any]]:
        """Pendentes de qualquer data e as demais desde `desde`, da mais recente para a mais antiga.
        `processos` None = todas do usuário; lista = só desses processos."""
        filtro: Dict[str, Any] = {
            "user_id": user_id,
            "$or": [{"situacao": "pendente"}, {"data_disponibilizacao": {"$gte": desde}}],
        }
        if processos is not None:
            filtro["numero_processo"] = {"$in": processos}
        cursor = self.publicacoes.find(filtro).sort([("data_disponibilizacao", DESCENDING), ("djen_id", DESCENDING)])
        return await cursor.limit(LIMITE_PUBLICACOES).to_list(length=LIMITE_PUBLICACOES)

    async def obter_publicacao(self, user_id: str, publicacao_id: str) -> Optional[Dict[str, Any]]:
        chave = oid(publicacao_id)
        if not chave:
            return None
        return await self.publicacoes.find_one({"_id": chave, "user_id": user_id})

    async def definir_situacao(self, user_id: str, publicacao_id: ObjectId, situacao: str, momento: str) -> None:
        await self.publicacoes.update_one({"_id": publicacao_id, "user_id": user_id},
                                          {"$set": {"situacao": situacao, "atualizada_em": momento}})

    # ------------------------------------------------------------ prazos
    async def criar_prazo(self, documento: Dict[str, Any]) -> Dict[str, Any]:
        await self.garantir_indices()
        documento = {"_id": ObjectId(), **documento}
        await self.prazos.insert_one(documento)
        return documento

    async def listar_prazos(self, user_id: str, caso_id: Optional[str] = None,
                            processos: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        filtro: Dict[str, Any] = {"user_id": user_id}
        if caso_id:
            filtro["$or"] = [{"caso_id": caso_id}, {"numero_processo": {"$in": processos or []}}]
        cursor = self.prazos.find(filtro).sort([("data_final", ASCENDING), ("criado_em", ASCENDING)])
        return await cursor.to_list(length=500)

    async def obter_prazo(self, user_id: str, prazo_id: str) -> Optional[Dict[str, Any]]:
        chave = oid(prazo_id)
        if not chave:
            return None
        return await self.prazos.find_one({"_id": chave, "user_id": user_id})

    async def atualizar_prazo(self, user_id: str, prazo_id: ObjectId, campos: Dict[str, Any]) -> None:
        await self.prazos.update_one({"_id": prazo_id, "user_id": user_id}, {"$set": campos})

    async def remover_prazo(self, user_id: str, prazo_id: ObjectId) -> None:
        await self.prazos.delete_one({"_id": prazo_id, "user_id": user_id})

    async def prazos_da_publicacao(self, user_id: str, publicacao_id: str) -> int:
        return len(await self.prazos.find({"user_id": user_id, "publicacao_id": publicacao_id}).to_list(length=50))
