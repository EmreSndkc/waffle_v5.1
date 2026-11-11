"""
Rapor bölümlerini (sections/*.md) birleştirir; .docx ve .pdf üretir.

    pip install python-docx markdown
    python docs/report/build_report.py

PDF için Google Chrome (headless) kullanılır. Diyagramlar okunabilirlik için
yatay (landscape) sayfalara yerleştirilir.
"""
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import markdown
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
SECTIONS = sorted((HERE / "sections").glob("*.md"))
NAME = "CSE321_Waffle_5.1_Report"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: A4; margin: 2cm 2cm 2cm 2cm; }
@page land { size: A4 landscape; margin: 1cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.4; color: #111; }
h1 { font-size: 19pt; margin: 0 0 6pt; }
h2 { font-size: 15pt; margin: 18pt 0 6pt; border-bottom: 1.5pt solid #1d3f7a; padding-bottom: 2pt; color: #1d3f7a; }
h3 { font-size: 12pt; margin: 12pt 0 4pt; }
p { margin: 0 0 7pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 10pt; font-size: 9.5pt; }
th, td { border: 0.75pt solid #777; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { background: #e6ecf7; }
tr { break-inside: avoid; }
code { font-family: Menlo, Consolas, monospace; font-size: 9pt; }
pre { background: #f4f4f4; border: 0.75pt solid #bbb; padding: 6pt 8pt; font-size: 9.5pt; line-height: 1.3; break-inside: avoid; white-space: pre-wrap; }
pre code { font-size: 9.5pt; }
figure { page: land; break-before: page; break-after: page; margin: 0; text-align: center; }
figure img { max-width: 100%; max-height: 17.6cm; }
figcaption { font-size: 11pt; font-weight: bold; margin-top: 5pt; }
"""


def to_html() -> str:
    text = "\n\n".join(p.read_text(encoding="utf-8") for p in SECTIONS)
    body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    # Tek başına duran resim paragrafı → yatay sayfada şekil
    body = re.sub(
        r'<p><img alt="([^"]*)" src="([^"]*)" ?/?></p>',
        lambda m: f'<figure><img src="{m.group(2).replace("../", "")}" alt=""><figcaption>{m.group(1)}</figcaption></figure>',
        body,
    )
    return body


class DocxBuilder(HTMLParser):
    """markdown'ın ürettiği sınırlı HTML alt kümesini python-docx'e çevirir."""

    def __init__(self, doc):
        super().__init__(convert_charrefs=True)
        self.doc, self.par, self.styles = doc, None, []
        self.table_rows, self.row, self.cell, self.in_pre = None, None, None, False
        self.figure_src = None

    # -- yardımcılar ---------------------------------------------------------
    def run(self, text):
        if self.cell is not None:
            self.cell.append((text, tuple(self.styles)))
            return
        if self.par is None:
            return
        r = self.par.add_run(text)
        r.bold = "b" in self.styles or None
        r.italic = "i" in self.styles or None
        if "code" in self.styles or self.in_pre:
            r.font.name = "Menlo"
            r.font.size = Pt(9.5 if self.in_pre else 9)

    def orient(self, landscape):
        s = self.doc.add_section(WD_SECTION.NEW_PAGE)
        w, h = sorted([s.page_width, s.page_height])
        s.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
        s.page_width, s.page_height = (h, w) if landscape else (w, h)
        m = Cm(1) if landscape else Cm(2)
        s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = m

    # -- etiketler -----------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h1", "h2", "h3"):
            self.par = self.doc.add_heading(level=int(tag[1]))
        elif tag == "p" and self.cell is None:
            self.par = self.doc.add_paragraph()
        elif tag == "li":
            self.par = self.doc.add_paragraph(style="List Bullet")
        elif tag == "pre":
            self.in_pre = True
            self.par = self.doc.add_paragraph()
            self.par.paragraph_format.left_indent = Cm(0.4)
            shade = OxmlElement("w:shd")
            shade.set(qn("w:val"), "clear"); shade.set(qn("w:fill"), "F0F0F0")
            self.par._p.get_or_add_pPr().append(shade)
        elif tag in ("strong", "b"):
            self.styles.append("b")
        elif tag in ("em", "i"):
            self.styles.append("i")
        elif tag == "code":
            self.styles.append("code")
        elif tag == "table":
            self.table_rows = []
        elif tag == "tr":
            self.row = []
        elif tag in ("th", "td"):
            self.cell = []
        elif tag == "figure":
            self.orient(True)
        elif tag == "img":
            self.figure_src = a["src"]
        elif tag == "figcaption":
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(HERE.parent / self.figure_src), height=Cm(16.8))
            self.par = self.doc.add_paragraph()
            self.par.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self.styles.append("b")

    def handle_endtag(self, tag):
        if tag in ("strong", "b", "em", "i", "code") and self.styles:
            self.styles.pop()
        elif tag == "pre":
            self.in_pre = False
        elif tag in ("th", "td"):
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr":
            self.table_rows.append(self.row)
        elif tag == "table":
            self.flush_table()
        elif tag == "figcaption":
            self.styles.pop()
        elif tag == "figure":
            self.orient(False)

    def handle_data(self, data):
        if self.in_pre:
            self.run(data.rstrip("\n"))
        elif data.strip() or (data and self.cell is None and self.par is not None and data != "\n"):
            self.run(data)

    def flush_table(self):
        rows = self.table_rows
        table = self.doc.add_table(rows=len(rows), cols=len(rows[0]))
        table.style = "Table Grid"
        width = table._tbl.tblPr.find(qn("w:tblW"))   # tablo sayfa genişliğini doldursun
        if width is None:
            width = OxmlElement("w:tblW")
            table._tbl.tblPr.append(width)
        width.set(qn("w:type"), "pct"); width.set(qn("w:w"), "5000")
        for i, row in enumerate(rows):
            for j, cell in enumerate(row):
                par = table.cell(i, j).paragraphs[0]
                for text, styles in cell:
                    r = par.add_run(text)
                    r.font.size = Pt(9.5)
                    r.bold = True if (i == 0 or "b" in styles) else None
                    if "code" in styles:
                        r.font.name = "Menlo"
                        r.font.size = Pt(8.5)
                if i == 0:
                    shade = OxmlElement("w:shd")
                    shade.set(qn("w:val"), "clear"); shade.set(qn("w:fill"), "E6ECF7")
                    table.cell(i, j)._tc.get_or_add_tcPr().append(shade)
        self.doc.add_paragraph()
        self.table_rows = None


def build_docx(body: str, out: Path):
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Helvetica", Pt(11)
    for level, size in ((1, 19), (2, 15), (3, 12)):
        st = doc.styles[f"Heading {level}"]
        st.font.name, st.font.size, st.font.bold = "Helvetica", Pt(size), True
        st.font.color.rgb = RGBColor(0x1D, 0x3F, 0x7A) if level == 2 else RGBColor(0x11, 0x11, 0x11)
    DocxBuilder(doc).feed(body)
    doc.save(out)


def build_pdf(body: str, out: Path):
    html = HERE / "_report.html"
    html.write_text(f'<!doctype html><html lang="tr"><meta charset="utf-8"><base href="{HERE.parent.as_uri()}/"><style>{CSS}</style><body>{body}</body></html>', encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", html.as_uri()], check=True, capture_output=True)
    html.unlink()


if __name__ == "__main__":
    body = to_html()
    build_docx(body, HERE / f"{NAME}.docx")
    build_pdf(body, HERE / f"{NAME}.pdf")
    print("Yazıldı:", f"{NAME}.docx,", f"{NAME}.pdf")
    sys.exit(0)
