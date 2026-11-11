"""
CSE 321 sunum slaytlarını üretir:

    pip install python-pptx
    python docs/slides/build_slides.py
"""
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
DIAGRAMS = HERE.parent / "diagrams"
OUT = HERE / "CSE321_Waffle_5.1_Slides.pptx"

NAVY, INK, MUTED, ACCENT = RGBColor(0x1D, 0x3F, 0x7A), RGBColor(0x11, 0x11, 0x11), RGBColor(0x55, 0x55, 0x55), RGBColor(0xA6, 0x1B, 0x1B)
SW, SH = Inches(13.333), Inches(7.5)

prs = Presentation()
prs.slide_width, prs.slide_height = SW, SH
BLANK = prs.slide_layouts[6]


def text(slide, x, y, w, h, lines, size=20, bold=False, color=INK, align=PP_ALIGN.LEFT, font="Helvetica"):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines if isinstance(lines, list) else [lines]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(size * 0.45)
        r = p.add_run()
        r.text = line
        r.font.size, r.font.bold, r.font.name = Pt(size), bold, font
        r.font.color.rgb = color
    return box


def new_slide(title, owner=None):
    s = prs.slides.add_slide(BLANK)
    bar = s.shapes.add_shape(1, 0, 0, SW, Inches(0.95))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    text(s, Inches(0.5), Inches(0.17), Inches(9.5), Inches(0.6), title, size=30, bold=True, color=RGBColor(255, 255, 255))
    if owner:
        text(s, Inches(9.8), Inches(0.28), Inches(3.1), Inches(0.5), owner, size=16, color=RGBColor(255, 255, 255), align=PP_ALIGN.RIGHT)
    return s


def picture(slide, name, top=Inches(1.1), bottom=Inches(0.15), left=Inches(0.3), right=Inches(0.3)):
    """Resmi oranını bozmadan kalan alana sığdırır ve ortalar."""
    path = DIAGRAMS / name
    iw, ih = Image.open(path).size
    aw, ah = SW - left - right, SH - top - bottom
    scale = min(aw / iw, ah / ih)
    w, h = int(iw * scale), int(ih * scale)
    slide.shapes.add_picture(str(path), left + (aw - w) // 2, top + (ah - h) // 2, w, h)


def table(slide, x, y, w, rows, col_widths, size=18, row_h=Inches(0.5)):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), x, y, w, row_h * len(rows))
    t = shape.table
    for j, cw in enumerate(col_widths):
        t.columns[j].width = int(w * cw)
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = t.cell(i, j)
            cell.text = value
            for p in cell.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size, r.font.name, r.font.bold = Pt(size), "Helvetica", i == 0
                    r.font.color.rgb = RGBColor(255, 255, 255) if i == 0 else INK
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if i == 0 else (RGBColor(0xF6, 0xF9, 0xFF) if i % 2 else RGBColor(255, 255, 255))
    return shape


# 1 — Özet
s = new_slide("Waffle 5.1 — PO Yönetim Sistemi")
text(s, Inches(0.6), Inches(1.25), Inches(12), Inches(0.9),
     ["CSE 321 Data & System Architecture · Waffle 5.1 fast (high)",
      "EmreSndkc · brkznqr · eminozkanca · Berkegn · github.com/EmreSndkc/waffle_v5.1"], size=18, color=MUTED)
text(s, Inches(0.6), Inches(2.45), Inches(12), Inches(0.7),
     "Her öğrencinin 11 Program Outcome (PO) puanını hesaplayan Django web sistemi.", size=26, bold=True)
text(s, Inches(0.6), Inches(3.35), Inches(12), Inches(0.6), "Not  →  (yüzdelerle) Learning Outcome  →  (1–5 ağırlıkla) Program Outcome", size=24)
text(s, Inches(0.6), Inches(4.05), Inches(12), Inches(0.7), "puan = Σ(ağırlık × puan) ÷ Σ ağırlık", size=30, bold=True, color=ACCENT, font="Menlo")
text(s, Inches(0.6), Inches(5.1), Inches(12), Inches(2), [
    "• Çalışıyor: veri modeli, hesaplama servisi, otomatik yeniden hesaplama, admin paneli, demo verisi",
    "• Kabul testi: Midterm 90, Project 80  →  PO1 = 85.0, PO2 = 82.9  (15 test, SQLite ve PostgreSQL)",
    "• Verisi olmayan PO 0 değil NULL: öğrenci haksız yere düşük görünmez"], size=20)

# 2 — Roller (D)
s = new_slide("Roller: kim neyi girer, kim neyi görür", "Berkegn")
picture(s, "roles.png")

# 3 — Mimari (A)
s = new_slide("Sistem mimarisi", "EmreSndkc")
picture(s, "architecture.png")

# 4 — ER (B)
s = new_slide("Veri modeli: ER diyagramı", "brkznqr")
picture(s, "er.png")

# 5 — Class (C)
s = new_slide("Class diyagramı", "eminozkanca")
picture(s, "class.png")

# 6 — Hesaplama örneği (C)
s = new_slide("Hesaplama örneği ve tutarlılık", "eminozkanca")
text(s, Inches(0.5), Inches(1.15), Inches(12.3), Inches(0.5),
     "Midterm 90, Project 80 · Midterm→LO1 %60, Project→LO1 %40, Midterm→LO2 %40, Project→LO2 %100", size=18, color=MUTED)
table(s, Inches(0.5), Inches(1.75), Inches(12.3), [
    ["Adım", "Hesap", "Sonuç"],
    ["LO1", "(0.60 × 90 + 0.40 × 80) ÷ (0.60 + 0.40)", "86.0"],
    ["LO2", "(0.40 × 90 + 1.00 × 80) ÷ (0.40 + 1.00)", "82.9"],
    ["PO1", "(2 × 86.0 + 1 × 82.86) ÷ (2 + 1)", "85.0"],
    ["PO2", "(2 × 82.86) ÷ 2", "82.9"],
    ["PO3", "bağlı LO yok", "NULL (veri yok)"],
], [0.12, 0.63, 0.25], size=20, row_h=Inches(0.52))
text(s, Inches(0.5), Inches(5.1), Inches(12.3), Inches(2.2), [
    "• LO→PO ağırlığı 1–5 tam sayı: örnekteki 1.0 : 0.5 : 1.0 oranı 2 : 1 : 2 olarak girilir, sonuç aynı",
    "• Not, eşleme ya da ağırlık değişince yalnızca etkilenen öğrenciler yeniden hesaplanır (signals)",
    "• Değişiklik + hesaplama tek transaction (transaction.atomic); öğrenci satırı select_for_update ile kilitlenir",
    "• PostgreSQL READ COMMITTED: kilit, eşzamanlı iki hesaplamanın birbirini ezmesini önler"], size=19)

# 7 — Sonraki adımlar
s = new_slide("Sonraki adımlar")
table(s, Inches(0.5), Inches(1.3), Inches(12.3), [
    ["Sprint", "İş", "Neden"],
    ["S1", "Giriş + rol bazlı yönlendirme, sahiplik kontrolü, CI (GitHub Actions)", "Hoca yalnızca kendi dersini, öğrenci yalnızca kendini görsün"],
    ["S2", "Ders/LO/değerlendirme kurulum ve not girme ekranları", "Admin paneli yerine role özel ekranlar"],
    ["S3", "Öğrenci PO paneli, Excel/CSV toplu not yükleme", "60 kişilik sınıf tek dosyada"],
    ["S4–S5", "Bölüm başkanı ısı haritası, PDF rapor, e-posta uyarısı", "Redis cache ve SMTP burada devreye girer"],
    ["S6", "Gerçekçi hacimle ölçüm (500 öğrenci, 40 ders)", "Tablo boyutları ve index etkisi final raporunda"],
], [0.1, 0.5, 0.4], size=17, row_h=Inches(0.72))
text(s, Inches(0.5), Inches(6.0), Inches(12.3), Inches(1.2), [
    "Açık konular: Assessment.max_score hesaba katılmıyor · resmi 11 PO metni doğrulanacak · eşzamanlılık testi yazılacak"],
     size=18, color=ACCENT)

prs.save(OUT)
print("Yazıldı:", OUT.name, f"({len(prs.slides)} slayt)")
