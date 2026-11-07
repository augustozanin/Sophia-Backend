"""
Resumo do consumo de IA de um caso (coleção `consumo_ia`) e custo estimado.

Os preços não ficam no código porque mudam: SOPHIA_PRECO_IA_USD traz o preço em dólar por
milhão de tokens no formato "entrada,entrada_cache,saida". Ex. do gpt-6-luna: "0.10,0.01,0.50".
Tokens de raciocínio já vêm somados na saída pelos provedores e são cobrados como saída.
Um 4º valor opcional é o preço por mil pesquisas na web (OpenAI: 10), ex.: "0.10,0.01,0.50,10".
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

CAMPOS = ("chamadas", "entrada", "entrada_cache", "saida", "raciocinio", "buscas")


def precos_por_milhao() -> Optional[Dict[str, float]]:
    bruto = (os.environ.get("SOPHIA_PRECO_IA_USD") or "").strip()
    if not bruto:
        return None
    try:
        valores = [float(x) for x in bruto.split(",")]
    except ValueError:
        return None
    if len(valores) not in (3, 4):
        return None
    entrada, cache, saida = valores[:3]
    busca = valores[3] if len(valores) == 4 else 0.0
    return {"entrada": entrada, "entrada_cache": cache, "saida": saida, "busca_por_mil": busca}


def custo_usd(uso: Dict[str, int], precos: Dict[str, float]) -> float:
    cache = min(uso.get("entrada_cache", 0), uso.get("entrada", 0))
    sem_cache = uso.get("entrada", 0) - cache
    tokens = (sem_cache * precos["entrada"] + cache * precos["entrada_cache"]
              + uso.get("saida", 0) * precos["saida"]) / 1_000_000
    buscas = uso.get("buscas", 0) * precos.get("busca_por_mil", 0.0) / 1000
    return round(tokens + buscas, 6)


def resumo_do_consumo(registros: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Totais por tarefa (análise, chat, peça...) e do caso inteiro."""
    por_tarefa: Dict[str, Dict[str, int]] = {}
    for r in registros:
        alvo = por_tarefa.setdefault(r.get("tarefa") or "outra", {k: 0 for k in CAMPOS})
        for k in CAMPOS:
            alvo[k] += int(r.get(k) or 0)
    total = {k: sum(t[k] for t in por_tarefa.values()) for k in CAMPOS}
    resposta: Dict[str, Any] = {
        "modelos": sorted({f"{r.get('provedor')}:{r.get('modelo')}" for r in registros}),
        "por_tarefa": por_tarefa,
        "total": total,
    }
    precos = precos_por_milhao()
    if precos:
        resposta["custo_usd"] = {t: custo_usd(u, precos) for t, u in por_tarefa.items()}
        resposta["custo_usd"]["total"] = custo_usd(total, precos)
    return resposta
