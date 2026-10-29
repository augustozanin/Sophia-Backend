"""
Monta o texto do caso que vai para a IA: relatos em ordem cronológica e documentos anexados
como dado não confiável (regra 7 do prompt), com limites de tamanho para caber no contexto do
modelo sem cortar no meio de uma palavra qualquer.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Tuple

from .document_utils import ExtractedDocument, detect_suspicious

LIMITE_RELATOS = 80_000
LIMITE_DOCUMENTO = 20_000
LIMITE_DOCUMENTOS = 60_000


def _origem(relato: Dict[str, Any]) -> str:
    return "escrito à mão, " if relato.get("origem") == "manual" else ""


def texto_dos_relatos(relatos: List[Dict[str, Any]], limite: int = LIMITE_RELATOS) -> str:
    """Um relato vai como está; vários ganham cabeçalho com a data. Se passar do limite,
    os mais antigos saem primeiro (o relato mais recente é o que reflete o caso hoje)."""
    validos = [r for r in relatos if str(r.get("texto") or "").strip()]
    if len(validos) == 1:
        return validos[0]["texto"].strip()[-limite:]
    blocos = [f"--- Relato {i + 1} ({_origem(r)}registrado em {r.get('criado_em') or 'data não informada'}) ---\n"
              f"{r['texto'].strip()}" for i, r in enumerate(validos)]
    escolhidos: List[str] = []
    total = 0
    for bloco in reversed(blocos):
        if total + len(bloco) > limite and escolhidos:
            escolhidos.append("[Relatos mais antigos omitidos por tamanho.]")
            break
        escolhidos.append(bloco[-limite:])
        total += len(bloco)
    return "\n\n".join(reversed(escolhidos))


def bloco_dos_documentos(documentos: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    """Devolve o bloco rotulado para o prompt e os metadados que ficam salvos na análise."""
    extraidos: List[ExtractedDocument] = []
    total = 0
    for doc in documentos:
        texto = str(doc.get("text") or "").strip()
        if not texto or total >= LIMITE_DOCUMENTOS:
            continue
        texto = texto[:min(LIMITE_DOCUMENTO, LIMITE_DOCUMENTOS - total)]
        total += len(texto)
        suspeitos = detect_suspicious(texto)
        extraidos.append(ExtractedDocument(
            filename=str(doc.get("name") or "documento"), text=texto,
            sha256=hashlib.sha256(texto.encode("utf-8")).hexdigest(),
            suspicious=bool(suspeitos), suspicious_matches=suspeitos))
    bloco = "\n\n".join(d.as_untrusted_block(i + 1) for i, d in enumerate(extraidos))
    meta = [{"nome": d.filename, "sha256": d.sha256, "suspeito": d.suspicious} for d in extraidos]
    return bloco, meta
