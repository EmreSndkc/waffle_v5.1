"""
Builds the joint CSE 311 + CSE 321 checkpoint deck (6 slides, no title slide):

    pip install python-pptx
    python docs/slides/build_slides.py            # whole deck
    python docs/slides/build_slides.py --only 3 out.pptx   # one slide, for visual checks
"""
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
OUT = HERE / "CSE321_Waffle_5.1_Slides.pptx"
TEAM = "Waffle 5.1 fast (high)"


def rgb(h):
    return RGBColor.from_string(h)


NAVY, INK, MUTED, ACCENT = rgb("1D3F7A"), rgb("111111"), rgb("555555"), rgb("A61B1B")
GREEN, ORANGE, PURPLE, WHITE = rgb("1D5A2B"), rgb("7A4A00"), rgb("5B3A8C"), rgb("FFFFFF")
PALE = {NAVY: rgb("EEF4FF"), GREEN: rgb("F0F9F1"), ORANGE: rgb("FFF5E6"), PURPLE: rgb("F3EEFA"),
        ACCENT: rgb("FDEEEE"), MUTED: rgb("F2F3F5")}
SW, SH = Inches(13.333), Inches(7.5)

prs = Presentation()
prs.slide_width, prs.slide_height = SW, SH
BLANK = prs.slide_layouts[6]
I = Inches


def text(slide, x, y, w, h, lines, size=20, bold=False, color=INK, align=PP_ALIGN.LEFT, font="Helvetica", anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    fill_text(box.text_frame, lines, size, bold, color, align, font, anchor)
    return box


def fill_text(tf, lines, size, bold, color, align, font="Helvetica", anchor=MSO_ANCHOR.TOP):
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = I(0.08)
    tf.margin_top = tf.margin_bottom = I(0.04)
    for i, line in enumerate(lines if isinstance(lines, list) else [lines]):
        # a line may be (text, size, bold, color) to override the defaults
        t, s, b, c = line if isinstance(line, tuple) else (line, size, bold, color)
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(s * 0.3)
        r = p.add_run()
        r.text = t
        r.font.size, r.font.bold, r.font.name = Pt(s), b, font
        r.font.color.rgb = c


def card(slide, x, y, w, h, lines, color=NAVY, size=16, align=PP_ALIGN.CENTER, solid=False, anchor=MSO_ANCHOR.MIDDLE):
    """Rounded box. lines[0] is the title (bold, in the card colour)."""
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, I(x), I(y), I(w), I(h))
    s.adjustments[0] = 0.08
    s.fill.solid()
    s.fill.fore_color.rgb = color if solid else PALE[color]
    s.line.color.rgb = color
    s.line.width = Pt(1.75)
    s.shadow.inherit = False
    lines = lines if isinstance(lines, list) else [lines]
    styled = [(lines[0], size + 2, True, WHITE if solid else color)]
    styled += [l if isinstance(l, tuple) else (l, size, False, WHITE if solid else INK) for l in lines[1:]]
    fill_text(s.text_frame, styled, size, False, INK, align, anchor=anchor)
    return s


def arrow(slide, x1, y1, x2, y2, color=INK, both=False, dashed=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x1), I(y1), I(x2), I(y2))
    c.line.color.rgb = color
    c.line.width = Pt(2.25)
    if dashed:
        c.line.dash_style = 4  # MSO_LINE.DASH
    ln = c.line._get_or_add_ln()
    for tag in ("a:tailEnd",) + (("a:headEnd",) if both else ()):
        end = ln.makeelement(qn(tag), {"type": "triangle", "w": "med", "len": "med"})
        ln.append(end)
    return c


def new_slide(n, course, title):
    s = prs.slides.add_slide(BLANK)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, I(1.05))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    text(s, 0.45, 0.08, 9, 0.3, course, size=13, bold=True, color=rgb("BFD0EE"))
    text(s, 0.45, 0.33, 10.5, 0.65, title, size=30, bold=True, color=WHITE)
    text(s, 9.6, 0.36, 3.3, 0.5, TEAM, size=15, color=WHITE, align=PP_ALIGN.RIGHT)
    text(s, 0.45, 7.08, 10, 0.3, "EmreSndkc · brkznqr · eminozkanca · Berkegn   ·   github.com/EmreSndkc/waffle_v5.1", size=11, color=MUTED)
    text(s, 11.9, 7.08, 1.0, 0.3, f"{n} / 6", size=11, color=MUTED, align=PP_ALIGN.RIGHT)
    return s


def table(slide, x, y, w, rows, col_widths, size=16, row_h=0.55):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), I(x), I(y), I(w), I(row_h * len(rows)))
    t = shape.table
    for j, cw in enumerate(col_widths):
        t.columns[j].width = int(I(w) * cw)
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = t.cell(i, j)
            cell.text = value
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for p in cell.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size, r.font.name, r.font.bold = Pt(size), "Helvetica", i == 0 or j == 0
                    r.font.color.rgb = WHITE if i == 0 else INK
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if i == 0 else (rgb("F6F9FF") if i % 2 else WHITE)
    return shape


def stat(slide, x, y, w, number, label, color=NAVY):
    text(slide, x, y, w, 0.9, number, size=44, bold=True, color=color, align=PP_ALIGN.CENTER)
    text(slide, x, y + 0.85, w, 0.8, label, size=14, color=MUTED, align=PP_ALIGN.CENTER)


# ------------------------------------------------------------------------------
def slide_1():
    s = new_slide(1, "CSE 311 · PUNCHLINE", "Grades in, 11 Program Outcome scores out")
    text(s, 0.6, 1.3, 12.1, 1.0,
         "Waffle 5.1 turns the grades an instructor enters into every student's Program Outcome (PO) profile, automatically.",
         size=22)
    y, h = 2.65, 1.75
    card(s, 0.6, y, 3.3, h, ["Assessments", "Midterm 90 · Project 80"], NAVY, 18)
    card(s, 5.0, y, 3.3, h, ["Learning Outcomes", "LO1 86.0 · LO2 82.9"], GREEN, 18)
    card(s, 9.4, y, 3.3, h, ["Program Outcomes", "PO1 85.0 · PO2 82.9"], ORANGE, 18)
    for x, label in ((3.9, "weights %"), (8.3, "weights 1–5")):
        arrow(s, x + 0.08, y + h / 2, x + 1.02, y + h / 2)
        text(s, x - 0.2, y + 0.35, 1.5, 0.4, label, size=12, color=MUTED, align=PP_ALIGN.CENTER)
    text(s, 0.6, 4.75, 12.1, 0.7, "score = Σ(weight × score) ÷ Σ weight", size=30, bold=True, color=ACCENT, align=PP_ALIGN.CENTER, font="Menlo")
    text(s, 0.6, 5.55, 12.1, 0.5, "Key ingredient: the same weighted average, applied twice.", size=20, align=PP_ALIGN.CENTER)
    text(s, 0.6, 6.2, 12.1, 0.5, "A PO with no data is NULL, not 0 — a student is never shown as failing an outcome nobody measured.",
         size=16, color=MUTED, align=PP_ALIGN.CENTER)


def slide_2():
    s = new_slide(2, "CSE 311 · BACKLOG & PROCESS", "How we work")
    cards = [
        ("Backlog", NAVY, ["16 features, 64 story points", "8 must-have (27) · 8 innovative (37)"]),
        ("Estimation", GREEN, ["Fibonacci story points", "1 · 2 · 3 · 5 · 8"]),
        ("Sprints", ORANGE, ["1 week", "planning → review → merge to main"]),
        ("Branching", PURPLE, ["feature/<name> → develop → main", "commits under the owner's name"]),
    ]
    for i, (title, color, lines) in enumerate(cards):
        card(s, 0.6 + i * 3.08, 1.45, 2.88, 2.1, [title] + lines, color, 15)
    stat(s, 0.6, 4.0, 3.9, "64 SP", "total backlog")
    stat(s, 4.7, 4.0, 3.9, "7 SP", "done in Sprint 0 (closed 11 Nov)", GREEN)
    stat(s, 8.8, 4.0, 3.9, "9.5 SP", "needed per sprint for the remaining six", ORANGE)
    text(s, 0.6, 6.2, 12.1, 0.6,
         "Process gap: the backlog is a table in our report today. Moving it to a GitHub Projects board is the first task of Sprint 1.",
         size=16, color=ACCENT, align=PP_ALIGN.CENTER)


def slide_3():
    s = new_slide(3, "CSE 311 · WORK & VELOCITY", "Who did what in Sprint 0")
    table(s, 0.6, 1.4, 12.1, [
        ["Member", "Code", "Diagram"],
        ["EmreSndkc", "Django skeleton, environment-driven settings", "System architecture"],
        ["brkznqr", "Model fixes: enrollment, constraints, indexes, migration", "ER diagram"],
        ["eminozkanca", "Calculation service, automatic recalculation, tests", "Class diagram"],
        ["Berkegn", "Demo data command, Django admin panel", "Role flow"],
    ], [0.17, 0.58, 0.25], size=17, row_h=0.62)
    stat(s, 0.6, 4.8, 3.9, "7 SP", "velocity: PO management (2) + calculation engine (5)", GREEN)
    stat(s, 4.7, 4.8, 3.9, "15", "tests pass on SQLite and PostgreSQL 18")
    stat(s, 8.8, 4.8, 3.9, "4 / 4", "members with code and docs commits", ORANGE)
    text(s, 0.6, 6.55, 12.1, 0.45, "Only fully finished features count; four features usable only through the admin panel are not counted.",
         size=14, color=MUTED, align=PP_ALIGN.CENTER)


def slide_4():
    s = new_slide(4, "CSE 321 · SYSTEM DESIGN", "Architecture: one Django server")
    card(s, 0.6, 2.9, 2.5, 1.7, ["Browser", "Django admin", "4 roles"], NAVY, 15)
    arrow(s, 3.15, 3.75, 4.05, 3.75, both=True)
    text(s, 3.0, 3.25, 1.2, 0.4, "HTTP", size=13, color=MUTED, align=PP_ALIGN.CENTER)
    card(s, 4.1, 1.45, 4.3, 5.3, ["Django application server"], GREEN, 16, anchor=MSO_ANCHOR.TOP)
    for i, lines in enumerate((["config/", "settings from environment variables"],
                               ["Admin panel", "login + role permissions"],
                               ["POCalculatorService", "grade → LO → PO"],
                               ["Models (Django ORM)", "10 tables"])):
        card(s, 4.35, 2.05 + i * 1.15, 3.8, 1.0, lines, GREEN, 13).fill.fore_color.rgb = WHITE
    ext = [("PostgreSQL", ["in use · SQLite fallback"], ORANGE, True, "SQL"),
           ("Redis cache", ["configured, not used yet"], MUTED, False, ""),
           ("SMTP e-mail", ["configured, not used yet"], MUTED, False, ""),
           ("File storage", ["configured, not used yet"], MUTED, False, "")]
    for i, (name, lines, color, live, label) in enumerate(ext):
        y = 1.45 + i * 1.36
        card(s, 9.5, y, 3.2, 1.2, [name] + lines, color, 14)
        arrow(s, 8.45, y + 0.6, 9.45, y + 0.6, color=INK if live else MUTED, both=live, dashed=not live)
        if label:
            text(s, 8.4, y + 0.15, 1.1, 0.4, label, size=13, color=MUTED, align=PP_ALIGN.CENTER)
    text(s, 0.5, 5.0, 3.5, 1.6, ["Every external component is chosen by an environment variable; without it a local fallback is used."],
         size=14, color=MUTED)


def slide_5():
    s = new_slide(5, "CSE 321 · DATA MODEL", "10 classes, two weighted mappings")
    y, h = 1.5, 1.0
    chain = [("StudentGrade", 1.6, NAVY), ("Assessment", 1.45, NAVY), ("Assessment_LO_Mapping", 2.6, ACCENT),
             ("LearningOutcome", 1.9, NAVY), ("LO_PO_Mapping", 1.75, ACCENT), ("ProgramOutcome", 1.85, NAVY)]
    x, gap = 0.5, 0.23
    for name, w, color in chain:
        card(s, x, y, w, h, [name], color, 11)
        if name != "ProgramOutcome":
            arrow(s, x + w, y + h / 2, x + w + gap, y + h / 2)
        if color is ACCENT:
            text(s, x, y + h + 0.02, w, 0.35, "weight %" if "Assessment" in name else "weight 1–5", size=13, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
        x += w + gap
    card(s, 0.5, 3.3, 1.75, h, ["User", "4 roles"], NAVY, 12)
    card(s, 2.9, 3.3, 1.75, h, ["Enrollment"], NAVY, 12)
    card(s, 5.3, 3.3, 1.75, h, ["Course", "owns assessments and LOs"], NAVY, 12)
    arrow(s, 2.88, 3.8, 2.3, 3.8)
    arrow(s, 4.67, 3.8, 5.25, 3.8)
    arrow(s, 1.3, 3.28, 1.3, 2.55, both=True)
    card(s, 0.5, 5.2, 2.2, 1.2, ["signals", "on save / delete"], PURPLE, 12)
    card(s, 3.35, 5.2, 3.0, 1.2, ["POCalculatorService", "reads the chain above"], GREEN, 12)
    card(s, 7.0, 5.2, 3.0, 1.2, ["StudentPOSnapshot", "student × PO · NULL = no data"], ORANGE, 12)
    arrow(s, 2.72, 5.8, 3.3, 5.8, dashed=True)
    arrow(s, 6.37, 5.8, 6.95, 5.8, dashed=True)
    text(s, 7.5, 3.2, 5.4, 1.9, [
        "• Grades and weights are stored once (normalized)",
        "• The snapshot is a precomputed PO profile; only the service writes it",
        "• Constraints: unique pairs, grade 0–100, weight 1–5"], size=15)
    text(s, 10.2, 5.35, 2.8, 1.0, "Dashboards read the snapshot, not the chain.", size=14, color=MUTED)


def slide_6():
    s = new_slide(6, "CSE 321 · CONSISTENCY  ·  CSE 311 · PROGRESS", "Always-fresh scores, and what comes next")
    steps = [("01  Change", "a grade, a mapping or a weight is saved or deleted"),
             ("02  Recalculate", "signals call the service for affected students only"),
             ("03  Commit together", "one transaction; student row locked (select_for_update)")]
    for i, (title, body) in enumerate(steps):
        card(s, 0.6 + i * 4.1, 1.4, 3.7, 1.45, [title, body], ACCENT, 13)
        if i < 2:
            arrow(s, 4.33 + i * 4.1, 2.12, 4.67 + i * 4.1, 2.12)
    card(s, 0.6, 3.2, 5.9, 3.0, ["Working today",
                                 "Data model with constraints and indexes",
                                 "PO calculation + automatic recalculation",
                                 "Django admin for every model",
                                 "Demo data: 11 POs, 3 courses, all roles",
                                 "15 tests, incl. the 90 / 80 example"], GREEN, 15, align=PP_ALIGN.LEFT)
    card(s, 6.8, 3.2, 5.9, 3.0, ["Next sprints",
                                 "S1  Login, role-based screens, ownership checks, CI",
                                 "S2  Course setup and grade entry screens",
                                 "S3  Student dashboard, bulk grade upload",
                                 "S4–S5  PDF reports, heat map, e-mail alerts",
                                 "S6  Measurements at realistic volume"], NAVY, 15, align=PP_ALIGN.LEFT)
    text(s, 0.6, 6.4, 12.1, 0.5,
         "Open items: no concurrency test yet · Assessment.max_score is not used · official text of the 11 POs to be verified",
         size=14, color=ACCENT, align=PP_ALIGN.CENTER)


SLIDES = [slide_1, slide_2, slide_3, slide_4, slide_5, slide_6]

if __name__ == "__main__":
    if "--only" in sys.argv:
        i = sys.argv.index("--only")
        SLIDES[int(sys.argv[i + 1]) - 1]()
        prs.save(sys.argv[i + 2])
    else:
        for build in SLIDES:
            build()
        prs.save(OUT)
        print("Written:", OUT.name, f"({len(prs.slides)} slides)")
