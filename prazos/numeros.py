"""
Validação e formatação do número da OAB e do número único de processo (CNJ).

Número CNJ (Resolução CNJ 65/2008): NNNNNNN-DD.AAAA.J.TR.OOOO, 20 dígitos. O dígito
verificador DD segue o ISO 7064 (módulo 97): conferir pega erro de digitação antes de
consultar o DJEN à toa.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

UFS = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB",
    "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
}


def so_digitos(valor: object) -> str:
    return re.sub(r"\D", "", str(valor or ""))


def normalizar_oab(numero: object, uf: object) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """(numero, uf, erro). O número fica só com dígitos e sem zeros à esquerda, como no DJEN."""
    digitos = so_digitos(numero).lstrip("0")
    sigla = str(uf or "").strip().upper()
    if not digitos or len(digitos) > 7:
        return None, None, "Informe o número da OAB (só os números)."
    if sigla not in UFS:
        return None, None, "Escolha a seccional (UF) da OAB."
    return digitos, sigla, None


def digito_verificador_cnj(numero: str) -> str:
    """DV de um número de 20 dígitos (as posições 8 e 9, do próprio DV, são ignoradas)."""
    base = numero[:7] + numero[9:] + "00"
    return f"{98 - int(base) % 97:02d}"


def normalizar_processo(numero: object) -> Tuple[Optional[str], Optional[str]]:
    """(20 dígitos, erro)."""
    digitos = so_digitos(numero)
    if len(digitos) != 20:
        return None, "O número do processo tem 20 dígitos (formato NNNNNNN-DD.AAAA.J.TR.OOOO)."
    if digito_verificador_cnj(digitos) != digitos[7:9]:
        return None, "Confira o número do processo: o dígito verificador não bate."
    return digitos, None


def formatar_processo(digitos: str) -> str:
    if len(digitos) != 20:
        return digitos
    return f"{digitos[:7]}-{digitos[7:9]}.{digitos[9:13]}.{digitos[13]}.{digitos[14:16]}.{digitos[16:]}"
