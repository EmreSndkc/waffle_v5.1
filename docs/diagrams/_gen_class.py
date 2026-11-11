"""Class diyagramını (class.svg) üretir:  python docs/diagrams/_gen_class.py"""
from pathlib import Path

W, RH, HH = 400, 27, 42
FS = 15
C1, C2, C3 = 90, 600, 1110
# ad: (x, y, stereotype, alanlar, metotlar)
T = {
    "User": (C1, 80, "AbstractUser", ["role: Role  (ADMIN, DEPT_HEAD, INSTRUCTOR, STUDENT)", "student_number: str  [0..1]", "username, first_name, last_name, email"], []),
    "Course": (C2, 80, "Model", ["code: str  {unique}", "title: str", "term: str"], []),
    "LearningOutcome": (C3, 80, "Model", ["code: str", "description: text"], []),
    "Enrollment": (C1, 360, "Model", ["enrolled_at: datetime"], []),
    "Assessment": (C2, 360, "Model", ["name: str", "max_score: Decimal"], []),
    "LO_PO_Mapping": (C3, 360, "Model", ["weight: int  {1..5}"], []),
    "StudentGrade": (C1, 640, "Model", ["score: Decimal  {0..100}", "updated_at: datetime"], []),
    "Assessment_LO_Mapping": (C2, 640, "Model", ["weight: Decimal  {> 0}"], []),
    "ProgramOutcome": (C3, 640, "Model", ["code: str  {unique, PO1..PO11}", "title: str", "description: text"], []),
    "StudentPOSnapshot": (C1, 930, "Model", ["score: Decimal  [0..1]  (None = veri yok)", "calculated_at: datetime"], []),
    "POCalculatorService": (C2, 900, "service", [], [
        "+ calculate_lo_scores(student): dict",
        "+ calculate_po_scores(lo_scores): dict",
        "+ calculate_student_profile(student)",
        "+ recalculate_students(student_ids): int",
        "+ save_grade(student, assessment, score)",
        "+ students_with_grades_for_assessment(id)",
        "+ students_with_grades_for_lo(id)"]),
    "signals": (C3, 930, "module", [], [
        "post_save / post_delete:",
        "  StudentGrade",
        "  Assessment_LO_Mapping",
        "  LO_PO_Mapping"]),
}


def h(n):
    _, _, _, a, m = T[n]
    return HH + 16 + (len(a) + len(m)) * RH + (10 if a and m else 0) + 8


def bot(n):
    return T[n][1] + h(n)


# İlişkiler: (noktalar, çocuk ucu etiketi, ebeveyn ucu etiketi, ad)
A = [
    ([(C2, 130), (C1 + W, 130)], "*", "0..1", "instructor"),
    ([(C3, 130), (C2 + W, 130)], "*", "1", ""),
    ([(C1 + 200, 360), (C1 + 200, bot("User"))], "*", "1", "student"),
    ([(C1 + W, 400), (545, 400), (545, 170), (C2, 170)], "*", "1", ""),
    ([(C2 + 200, 360), (C2 + 200, bot("Course"))], "*", "1", ""),
    ([(C3 + 200, 360), (C3 + 200, bot("LearningOutcome"))], "*", "1", ""),
    ([(C3 + 200, bot("LO_PO_Mapping")), (C3 + 200, 640)], "*", "1", ""),
    ([(C2 + 200, 640), (C2 + 200, bot("Assessment"))], "*", "1", ""),
    ([(C2 + W, 690), (1055, 690), (1055, 170), (C3, 170)], "*", "1", ""),
    ([(C1, 700), (55, 700), (55, 170), (C1, 170)], "*", "1", "student"),
    ([(C1 + W, 700), (545, 700), (545, 440), (C2, 440)], "*", "1", ""),
    ([(C1, 1000), (25, 1000), (25, 140), (C1, 140)], "*", "1", "student"),
    ([(C1 + 200, bot("StudentPOSnapshot")), (C1 + 200, 1190), (1545, 1190), (1545, 700), (C3 + W, 700)], "*", "1", ""),
]
# Bağımlılıklar (kesikli): (noktalar, etiket)
D = [
    ([(C3, 990), (C2 + W, 990)], "«çağırır»"),
    ([(C2, 990), (C1 + W, 990)], "«yazar»"),
    ([(C2 + 200, 900), (C2 + 200, bot("Assessment_LO_Mapping"))], "«okur»"),
]

o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1580 1280" font-family="Helvetica, Arial, sans-serif">',
     '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto"><path d="M0 0L10 5L0 10" fill="none" stroke="#333" stroke-width="1.5"/></marker></defs>',
     '<rect width="1580" height="1280" fill="#fff"/>',
     '<text x="790" y="42" text-anchor="middle" font-size="28" font-weight="bold" fill="#111">Waffle 5.1 — Class Diyagramı</text>']
for pts, child, parent, name in A:
    o.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="none" stroke="#333" stroke-width="2" marker-end="url(#a)"/>')
    (x0, y0), (x1, y1) = pts[0], pts[1]
    dx, dy = (x1 > x0) - (x1 < x0), (y1 > y0) - (y1 < y0)
    o.append(f'<text x="{x0 + dx*14 + (8 if dy else 0)}" y="{y0 + dy*20 - (6 if dx else -4)}" font-size="16" font-weight="bold" text-anchor="middle" fill="#a61b1b">{child}</text>')
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    dx, dy = (x1 > x0) - (x1 < x0), (y1 > y0) - (y1 < y0)
    o.append(f'<text x="{x1 - dx*(26 if len(parent) == 1 else 38) + (16 if dy else 0)}" y="{y1 - dy*22 - (6 if dx else -6)}" font-size="16" font-weight="bold" text-anchor="middle" fill="#a61b1b">{parent}</text>')
for pts, label in D:
    o.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="none" stroke="#333" stroke-width="2" stroke-dasharray="7 5" marker-end="url(#a)"/>')
    mx, my = (pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2
    if pts[0][0] == pts[1][0]:
        o.append(f'<text x="{mx + 8}" y="{my + 5}" font-size="15" font-style="italic" fill="#111">{label}</text>')
    else:
        o.append(f'<text x="{mx}" y="{my - 8}" font-size="15" font-style="italic" text-anchor="middle" fill="#111">{label}</text>')
for name, (x, y, st, attrs, methods) in T.items():
    head, fill = {"service": ("#1d5a2b", "#f0f9f1"), "module": ("#6b3fa0", "#f7f1fd")}.get(st, ("#1d3f7a", "#f6f9ff"))
    if name == "StudentPOSnapshot":
        head, fill = "#7a4a00", "#fff5e6"
    o.append(f'<rect x="{x}" y="{y}" width="{W}" height="{h(name)}" fill="{fill}" stroke="{head}" stroke-width="2"/>')
    o.append(f'<rect x="{x}" y="{y}" width="{W}" height="{HH+16}" fill="{head}"/>')
    o.append(f'<text x="{x+W/2}" y="{y+20}" text-anchor="middle" font-size="14" font-style="italic" fill="#fff">«{st}»</text>')
    o.append(f'<text x="{x+W/2}" y="{y+45}" text-anchor="middle" font-size="20" font-weight="bold" fill="#fff">{name}</text>')
    ty = y + HH + 16 + 20
    for a in attrs:
        o.append(f'<text x="{x+12}" y="{ty}" font-size="15.5" fill="#111">{a}</text>')
        ty += RH
    if attrs and methods:
        o.append(f'<line x1="{x}" y1="{ty-14}" x2="{x+W}" y2="{ty-14}" stroke="{head}" stroke-width="1.5"/>')
        ty += 10
    for m in methods:
        o.append(f'<text x="{x+12}" y="{ty}" font-size="15.5" fill="#111" xml:space="preserve">{m}</text>')
        ty += RH
o.append('<text x="90" y="1240" font-size="17" fill="#111">Düz ok: ilişki (ForeignKey), <tspan font-weight="bold" fill="#a61b1b">*</tspan> → <tspan font-weight="bold" fill="#a61b1b">1</tspan>.  Kesikli ok: bağımlılık.  signals, kayıt değişince servisi çağırır; servis kaynak tabloları okur, snapshot\'ı yazar.</text>')
o.append("</svg>")
Path(__file__).with_name("class.svg").write_text("\n".join(o), encoding="utf-8")
