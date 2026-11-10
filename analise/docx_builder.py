"""Converte a minuta salva em .docx no padrão usual das petições.

Leiaute: A4, margens de 3 cm (superior e esquerda) e 2 cm (inferior e direita), Times New Roman 12,
espaçamento 1,5, texto justificado com recuo de primeira linha, título da peça centralizado em
negrito, seções numeradas em romano, citações com recuo de 4 cm em corpo 11 e espaçamento simples,
pedidos em a), b), c), fecho com assinatura centralizada. Os dados a preencher ([NOME DO RÉU])
ficam destacados em amarelo. O aviso de minuta vai no cabeçalho e o número da página no rodapé.

O arquivo é montado em memória a cada download a partir do que está na coleção `pecas`: nada fica
gravado em disco no servidor. Minutas antigas (só texto) usam o mesmo leiaute, lendo o texto.
"""
from __future__ import annotations

import io
import re
import unicodedata
from typing import Any, Dict, Optional

from .minuta import letra, titulo_da_secao

AVISO = "MINUTA GERADA POR IA — REVISAR ANTES DE PROTOCOLAR"
FONTE = "Times New Roman"
_MARCADOR = re.compile(r"(\[[^\]\n]{1,80}\])")


class DocxIndisponivel(RuntimeError):
    """python-docx não instalado no ambiente do backend."""


class _Peca:
    """Documento com os estilos da peça e um método para cada tipo de parágrafo."""

    def __init__(self, base: Optional[bytes] = None):
        # Carregado só no download: sem o pacote, o resto do backend continua funcionando.
        try:
            import docx
            from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn
            from docx.shared import Cm, Pt, RGBColor
        except ImportError as e:
            raise DocxIndisponivel(
                "Download em .docx indisponível: instale as dependências com "
                "venv/Scripts/python -m pip install -r requirements.txt") from e

        self.Cm, self.Pt, self.RGB, self.qn, self.Oxml = Cm, Pt, RGBColor, qn, OxmlElement
        self.ALINHA = {"justificado": WD_ALIGN_PARAGRAPH.JUSTIFY, "centro": WD_ALIGN_PARAGRAPH.CENTER,
                       "esquerda": WD_ALIGN_PARAGRAPH.LEFT, "direita": WD_ALIGN_PARAGRAPH.RIGHT}
        self.AMARELO = WD_COLOR_INDEX.YELLOW
        if base and self._usar_base(docx, base):
            return
        self.d = docx.Document()
        secao = self.d.sections[0]
        secao.page_width, secao.page_height = Cm(21), Cm(29.7)
        secao.top_margin, secao.left_margin = Cm(3), Cm(3)
        secao.bottom_margin, secao.right_margin = Cm(2), Cm(2)
        secao.header_distance = secao.footer_distance = Cm(1.25)

        normal = self.d.styles["Normal"]
        normal.font.name = FONTE
        normal.font.size = Pt(12)
        normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONTE)
        formato = normal.paragraph_format
        formato.line_spacing = 1.5
        formato.space_before = Pt(0)
        formato.space_after = Pt(6)
        self._cabecalho_e_rodape(secao)

    def _usar_base(self, docx, base: bytes) -> bool:
        """Modelo .docx do escritório como base: mantém timbre (cabeçalho e rodapé), margens e
        fonte dele e troca só o corpo. Arquivo ilegível cai no leiaute padrão."""
        try:
            self.d = docx.Document(io.BytesIO(base))
        except Exception:  # noqa: BLE001
            return False
        corpo = self.d.element.body
        for elemento in list(corpo):
            if elemento.tag != self.qn("w:sectPr"):
                corpo.remove(elemento)
        # O cabeçalho é do escritório: o aviso de minuta vai no topo do corpo.
        aviso = self.d.add_paragraph()
        aviso.alignment = self.ALINHA["centro"]
        run = aviso.add_run(AVISO)
        run.bold = True
        run.font.size = self.Pt(8)
        run.font.color.rgb = self.RGB(0xA0, 0x30, 0x30)
        secao = self.d.sections[0]
        if not any(p.text.strip() for p in secao.footer.paragraphs):
            self._numero_da_pagina(secao)
        return True

    def _cabecalho_e_rodape(self, secao) -> None:
        aviso = secao.header.paragraphs[0]
        aviso.alignment = self.ALINHA["centro"]
        run = aviso.add_run(AVISO)
        run.bold = True
        run.font.size = self.Pt(8)
        run.font.color.rgb = self.RGB(0xA0, 0x30, 0x30)
        self._numero_da_pagina(secao)

    def _numero_da_pagina(self, secao) -> None:
        rodape = secao.footer.paragraphs[0] if secao.footer.paragraphs else secao.footer.add_paragraph()
        rodape.alignment = self.ALINHA["direita"]
        for parte in ("Página ", "PAGE", " de ", "NUMPAGES"):
            r = rodape.add_run()
            r.font.size = self.Pt(9)
            if parte not in ("PAGE", "NUMPAGES"):
                r.text = parte
                continue
            # Campo do Word que mostra o número da página (ou o total de páginas).
            for tipo in ("begin", None, "end"):
                if tipo:
                    el = self.Oxml("w:fldChar")
                    el.set(self.qn("w:fldCharType"), tipo)
                else:
                    el = self.Oxml("w:instrText")
                    el.set(self.qn("xml:space"), "preserve")
                    el.text = parte
                r._r.append(el)

    def _runs(self, paragrafo, texto: str, negrito: bool = False, italico: bool = False,
              tamanho: Optional[int] = None) -> None:
        for parte in _MARCADOR.split(texto):
            if not parte:
                continue
            r = paragrafo.add_run(parte)
            if negrito:
                r.bold = True
            if italico:
                r.italic = True
            if tamanho:
                r.font.size = self.Pt(tamanho)
            if _MARCADOR.fullmatch(parte):
                r.font.highlight_color = self.AMARELO
                r.bold = True

    def paragrafo(self, texto: str, recuo: bool = True, alinhamento: str = "justificado",
                  negrito: bool = False, antes: Optional[int] = None, depois: Optional[int] = None,
                  junto: bool = False):
        p = self.d.add_paragraph()
        p.alignment = self.ALINHA[alinhamento]
        formato = p.paragraph_format
        if recuo:
            formato.first_line_indent = self.Cm(2)
        if antes is not None:
            formato.space_before = self.Pt(antes)
        if depois is not None:
            formato.space_after = self.Pt(depois)
        if junto:
            formato.keep_with_next = True
        self._runs(p, texto, negrito=negrito)
        return p

    def enderecamento(self, texto: str) -> None:
        self.paragrafo(texto, recuo=False, negrito=True, depois=48)

    def titulo(self, texto: str) -> None:
        self.paragrafo(texto, recuo=False, alinhamento="centro", negrito=True, antes=12, depois=12, junto=True)

    def secao(self, texto: str) -> None:
        self.paragrafo(texto, recuo=False, alinhamento="esquerda", negrito=True, antes=12, junto=True)

    def subtitulo(self, texto: str) -> None:
        p = self.d.add_paragraph()
        p.paragraph_format.space_before = self.Pt(6)
        p.paragraph_format.keep_with_next = True
        self._runs(p, texto, negrito=True, italico=True)

    def citacao(self, texto: str, fonte: Optional[str] = None) -> None:
        p = self.d.add_paragraph()
        p.alignment = self.ALINHA["justificado"]
        formato = p.paragraph_format
        formato.left_indent = self.Cm(4)
        formato.line_spacing = 1.0
        formato.space_before, formato.space_after = self.Pt(6), self.Pt(12)
        self._runs(p, f"“{texto}”", italico=True, tamanho=11)
        if fonte:
            self._runs(p, f" ({fonte})", tamanho=11)

    def item(self, rotulo: str, texto: str) -> None:
        p = self.d.add_paragraph()
        p.alignment = self.ALINHA["justificado"]
        formato = p.paragraph_format
        formato.left_indent = self.Cm(2)
        formato.first_line_indent = self.Cm(-0.8)
        formato.tab_stops.add_tab_stop(self.Cm(2))
        self._runs(p, f"{rotulo}\t{texto}")

    def fecho(self, f: Dict[str, str]) -> None:
        self.paragrafo(f["encerramento"], antes=12, depois=18, junto=True)
        self.paragrafo(f["local_data"], recuo=False, alinhamento="centro", depois=48, junto=True)
        self.paragrafo("_" * 38, recuo=False, alinhamento="centro", depois=0, junto=True)
        self.paragrafo(f["advogado"], recuo=False, alinhamento="centro", negrito=True, depois=0, junto=True)
        self.paragrafo(f["oab"], recuo=False, alinhamento="centro", depois=0)

    def salvar(self) -> bytes:
        saida = io.BytesIO()
        self.d.save(saida)
        return saida.getvalue()


def _da_estrutura(doc: _Peca, m: Dict[str, Any]) -> None:
    if m.get("enderecamento"):
        doc.enderecamento(m["enderecamento"])
    if m.get("referencia"):
        doc.paragrafo(m["referencia"], recuo=False, negrito=True, depois=18)
    for p in m.get("qualificacao") or []:
        doc.paragrafo(p)
    doc.titulo(m["titulo"])
    if m.get("complemento_titulo"):
        doc.paragrafo(m["complemento_titulo"])
    for i, secao in enumerate(m["secoes"]):
        doc.secao(titulo_da_secao(i, secao["titulo"]))
        for bloco in secao["blocos"]:
            if bloco["tipo"] == "lista":
                for j, item in enumerate(bloco["itens"]):
                    doc.item(f"{letra(j)})", item)
            elif bloco["tipo"] == "citacao":
                doc.citacao(bloco["texto"], bloco.get("fonte"))
            elif bloco["tipo"] == "subtitulo":
                doc.subtitulo(bloco["texto"])
            else:
                doc.paragrafo(bloco["texto"])
    doc.fecho(m["fecho"])


def _do_texto(doc: _Peca, rascunho: str) -> None:
    """Minutas antigas, guardadas só como texto: mesmo leiaute, com títulos lidos pelas maiúsculas."""
    viu_secao = False
    for linha in rascunho.splitlines():
        texto = re.sub(r"^#+\s*", "", linha.strip()).replace("**", "").strip()
        if not texto or texto.upper() == AVISO:
            continue
        if not viu_secao and re.match(r"^minuta\b.*revis", texto, re.IGNORECASE):
            continue  # aviso escrito pela IA: o cabeçalho já traz o aviso
        if linha.strip().startswith("#") or (texto.isupper() and len(texto) < 90):
            if not viu_secao and texto.startswith(("EXCELENT", "EXMO", "ILUSTR", "AO ", "À ")):
                doc.enderecamento(texto)
            else:
                doc.secao(texto)
                viu_secao = True
        elif re.match(r"^[a-z]\)\s", texto):
            doc.item(texto[:2], texto[3:].strip())
        elif texto.startswith(("EXCELENT", "EXMO")) and not viu_secao:
            doc.enderecamento(texto)
        else:
            doc.paragrafo(texto)


def build_docx(rascunho: str, estrutura: Optional[Dict[str, Any]] = None,
               base: Optional[bytes] = None) -> bytes:
    """`base`: .docx do modelo do escritório, para manter o timbre e a formatação dele."""
    doc = _Peca(base)
    if estrutura:
        _da_estrutura(doc, estrutura)
    else:
        _do_texto(doc, rascunho)
    return doc.salvar()


def nome_do_arquivo(titulo: str) -> str:
    ascii_ = unicodedata.normalize("NFKD", titulo).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "-", ascii_).strip("-").lower()
    return f"minuta-{base or 'peca'}.docx"
