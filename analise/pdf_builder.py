"""PDF da minuta revisada, montado em memória (A4, Times-Roman, acentos em Windows-1252)."""
from __future__ import annotations

from typing import List

from .docx_builder import nome_do_arquivo

COLUNAS = 90
LINHAS_POR_PAGINA = 48
ENTRELINHA = 15

_EXTRAS = {
    "\u2014": "-",
    "\u2013": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u00a0": " ",
}


def _win1252(texto: str) -> str:
    saida = []
    for ch in texto:
        if ch in _EXTRAS:
            saida.append(_EXTRAS[ch])
            continue
        c = ord(ch)
        if c == 9:
            saida.append("  ")
            continue
        if c in (10, 13):
            saida.append(ch)
            continue
        if c < 32:
            continue
        saida.append(ch if c <= 255 else "?")
    return "".join(saida)


def _escapar(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _linhas(texto: str) -> List[str]:
    linhas: List[str] = []
    for bruta in _win1252(texto).replace("\r\n", "\n").split("\n"):
        if not bruta:
            linhas.append("")
            continue
        resto = bruta
        while len(resto) > COLUNAS:
            corte = resto.rfind(" ", 0, COLUNAS)
            if corte < COLUNAS // 2:
                corte = COLUNAS
            linhas.append(resto[:corte])
            resto = resto[corte:].lstrip()
        linhas.append(resto)
    return linhas


def build_pdf(rascunho: str) -> bytes:
    linhas = _linhas((rascunho or "").strip() or " ")
    paginas = [linhas[i:i + LINHAS_POR_PAGINA] for i in range(0, len(linhas), LINHAS_POR_PAGINA)] or [[""]]

    partes: List[bytes] = []
    tamanho = 0
    offsets = [0]

    def escrever(s: str | bytes) -> None:
        nonlocal tamanho
        buf = s if isinstance(s, bytes) else s.encode("latin-1")
        partes.append(buf)
        tamanho += len(buf)

    def obj(n: int, corpo: str) -> None:
        while len(offsets) <= n:
            offsets.append(0)
        offsets[n] = tamanho
        escrever(f"{n} 0 obj\n{corpo}\nendobj\n")

    escrever("%PDF-1.4\n")
    obj(1, "<< /Type /Catalog /Pages 2 0 R >>")
    ids = [4 + i * 2 for i in range(len(paginas))]
    obj(2, f"<< /Type /Pages /Count {len(paginas)} /Kids [{' '.join(f'{i} 0 R' for i in ids)}] >>")
    obj(3, "<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman >>")

    for i, pagina in enumerate(paginas):
        id_pagina = 4 + i * 2
        id_fluxo = id_pagina + 1
        desenho = "\n".join([
            "BT",
            "/F1 12 Tf",
            f"{ENTRELINHA} TL",
            "72 770 Td",
            *[
                f"({_escapar(linha)}) Tj" if j == 0 else f"T* ({_escapar(linha)}) Tj"
                for j, linha in enumerate(pagina)
            ],
            "ET",
        ]).encode("latin-1")
        obj(
            id_pagina,
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {id_fluxo} 0 R >>",
        )
        while len(offsets) <= id_fluxo:
            offsets.append(0)
        offsets[id_fluxo] = tamanho
        escrever(f"{id_fluxo} 0 obj\n<< /Length {len(desenho)} >>\nstream\n")
        escrever(desenho)
        escrever("\nendstream\nendobj\n")

    inicio = tamanho
    total = len(offsets)
    escrever(f"xref\n0 {total}\n")
    escrever("0000000000 65535 f \n")
    for i in range(1, total):
        escrever(f"{offsets[i]:010d} 00000 n \n")
    escrever(f"trailer << /Size {total} /Root 1 0 R >>\nstartxref\n{inicio}\n%%EOF\n")
    return b"".join(partes)


def nome_do_pdf(titulo: str) -> str:
    return nome_do_arquivo(titulo, "pdf")
