"""PDF da minuta em UTF-8, Times New Roman, margens da petição (A4)."""
from __future__ import annotations

import re
from pathlib import Path

from .docx_builder import nome_do_arquivo

MARGEM_ESQ = 30.0
MARGEM_DIR = 20.0
MARGEM_SUP = 30.0
MARGEM_INF = 20.0
TAMANHO = 12
# 12 pt × 1,5, em milímetros.
ALTURA = 6.35

_PASTA = Path(__file__).resolve().parent / "fontes"
_FALLBACKS = (
    Path(r"C:\Windows\Fonts"),
    Path("/usr/share/fonts/truetype/liberation"),
)


def _arquivo_fonte(*nomes: str) -> str:
    for nome in nomes:
        for pasta in (_PASTA, *_FALLBACKS):
            caminho = pasta / nome
            if caminho.is_file():
                return str(caminho)
    raise RuntimeError("Fonte Times da minuta não encontrada.")


def _eh_maiusculas(texto: str) -> bool:
    letras = [ch for ch in texto if ch.isalpha()]
    return bool(letras) and all(ch.upper() == ch for ch in letras)


def _eh_enderecamento(texto: str) -> bool:
    t = texto.upper()
    return t.startswith(("EXCELENT", "EXMO", "ILUSTR", "AO ", "À "))


def _eh_secao(texto: str) -> bool:
    return bool(re.match(r"^[IVXLCDM]+\s*[-–—]\s+", texto))


def _eh_item(texto: str) -> bool:
    return bool(re.match(r"^[a-z]\)\s", texto))


def _eh_titulo_peca(texto: str) -> bool:
    return (
        _eh_maiusculas(texto)
        and 3 < len(texto) < 90
        and not _eh_enderecamento(texto)
        and not _eh_secao(texto)
    )


def _eh_fecho_central(texto: str, depois_do_pedido: bool) -> bool:
    baixo = texto.lower()
    if baixo.startswith("nestes termos") or "pede deferimento" in baixo:
        return True
    return depois_do_pedido and len(texto) < 80


def build_pdf(rascunho: str) -> bytes:
    from fpdf import FPDF

    pdf = FPDF(format="A4", unit="mm")
    pdf.set_lang("pt-BR")
    pdf.set_title("Minuta")
    pdf.set_margins(MARGEM_ESQ, MARGEM_SUP, MARGEM_DIR)
    pdf.set_auto_page_break(auto=True, margin=MARGEM_INF)
    pdf.add_font("TimesBR", fname=_arquivo_fonte("times.ttf", "LiberationSerif-Regular.ttf"))
    pdf.add_font("TimesBR", style="B", fname=_arquivo_fonte("timesbd.ttf", "LiberationSerif-Bold.ttf"))
    pdf.add_page()

    viu_secao = False
    depois_do_pedido = False

    def escrever(texto: str, alinhamento: str, negrito: bool) -> None:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("TimesBR", style="B" if negrito else "", size=TAMANHO)
        pdf.multi_cell(w=pdf.epw, h=ALTURA, text=texto, align=alinhamento)

    for bruta in (rascunho or "").replace("\r\n", "\n").split("\n"):
        texto = re.sub(r"^#+\s*", "", bruta.strip()).replace("**", "").strip()
        if not texto:
            pdf.ln(ALTURA / 2)
            continue
        if _eh_fecho_central(texto, depois_do_pedido):
            depois_do_pedido = True
            escrever(texto, "C", False)
            continue
        if not viu_secao and _eh_enderecamento(texto):
            escrever(texto, "L", True)
            continue
        if _eh_titulo_peca(texto) and not viu_secao:
            escrever(texto, "C", True)
            continue
        if _eh_secao(texto) or (_eh_maiusculas(texto) and len(texto) < 90):
            viu_secao = True
            escrever(texto, "L", True)
            continue
        if _eh_item(texto):
            escrever(texto, "J", False)
            continue
        escrever(texto, "J", False)

    saida = pdf.output()
    return bytes(saida)


def nome_do_pdf(titulo: str) -> str:
    return nome_do_arquivo(titulo, "pdf")
