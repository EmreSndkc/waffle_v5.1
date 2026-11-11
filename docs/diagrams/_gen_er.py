"""ER diyagramını (er.svg) üretir:  python docs/diagrams/_gen_er.py"""
from pathlib import Path

W, RH, HH = 430, 28, 42
C1, C2, C3 = 90, 630, 1170
T = {
    "User": (C1, 80, ["PK  id", "UQ  username", "    role  (4 values: ADMIN … STUDENT)", "UQ  student_number  (nullable)", "    first_name, last_name, email, password", "IX  (role)"]),
    "Course": (C2, 80, ["PK  id", "UQ  code", "    title", "    term", "FK  instructor_id → User  (nullable)"]),
    "LearningOutcome": (C3, 80, ["PK  id", "FK  course_id → Course", "    code", "    description", "UQ  (course_id, code)"]),
    "Enrollment": (C1, 360, ["PK  id", "FK  student_id → User", "FK  course_id → Course", "    enrolled_at", "UQ  (student_id, course_id)", "IX  (course_id, student_id)"]),
    "Assessment": (C2, 360, ["PK  id", "FK  course_id → Course", "    name", "    max_score", "UQ  (course_id, name)"]),
    "LO_PO_Mapping": (C3, 360, ["PK  id", "FK  learning_outcome_id → LearningOutcome", "FK  program_outcome_id → ProgramOutcome", "    weight  smallint, CHECK 1–5", "UQ  (learning_outcome_id, program_outcome_id)", "IX  (program_outcome_id, learning_outcome_id)"]),
    "StudentGrade": (C1, 640, ["PK  id", "FK  student_id → User", "FK  assessment_id → Assessment", "    score  decimal(5,2), CHECK 0–100", "    updated_at", "UQ  (student_id, assessment_id)", "IX  (assessment_id, student_id)"]),
    "Assessment_LO_Mapping": (C2, 640, ["PK  id", "FK  assessment_id → Assessment", "FK  learning_outcome_id → LearningOutcome", "    weight  decimal(5,2), CHECK > 0", "UQ  (assessment_id, learning_outcome_id)", "IX  (learning_outcome_id, assessment_id)"]),
    "ProgramOutcome": (C3, 640, ["PK  id", "UQ  code  (PO1 … PO11)", "    title", "    description"]),
    "StudentPOSnapshot": (C1, 950, ["PK  id", "FK  student_id → User", "FK  program_outcome_id → ProgramOutcome", "    score  decimal(5,2), NULL = no data", "    calculated_at", "UQ  (student_id, program_outcome_id)", "IX  (program_outcome_id, score)"]),
}


def h(name):
    return HH + len(T[name][2]) * RH + 8


def bottom(name):
    return T[name][1] + h(name)


# FK okları: çocuk tablo → başvurulan tablo (N → 1)
E = [
    [(C2, 150), (C1 + W, 150)],
    [(C3, 150), (C2 + W, 150)],
    [(C1 + 200, 360), (C1 + 200, bottom("User"))],
    [(C1 + W, 440), (575, 440), (575, 250), (C2, 250)],
    [(C2 + 200, 360), (C2 + 200, bottom("Course"))],
    [(C3 + 200, 360), (C3 + 200, bottom("LearningOutcome"))],
    [(C3 + 200, bottom("LO_PO_Mapping")), (C3 + 200, 640)],
    [(C2 + 200, 640), (C2 + 200, bottom("Assessment"))],
    [(C2 + W, 720), (1115, 720), (1115, 230), (C3, 230)],
    [(C1, 720), (55, 720), (55, 200), (C1, 200)],
    [(C1 + W, 720), (575, 720), (575, 480), (C2, 480)],
    [(C1, 1050), (25, 1050), (25, 160), (C1, 160)],
    [(C1 + W, 1050), (C3 + 200, 1050), (C3 + 200, bottom("ProgramOutcome"))],
]

o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 60 1650 1190" font-family="Helvetica, Arial, sans-serif">',
     '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto"><path d="M0 0L10 5L0 10z" fill="#333"/></marker></defs>',
     '<rect width="1650" height="1250" fill="#fff"/>',]
for pts in E:
    d = " ".join(f"{x},{y}" for x, y in pts)
    o.append(f'<polyline points="{d}" fill="none" stroke="#333" stroke-width="2" marker-end="url(#a)"/>')
for name, (x, y, rows) in T.items():
    snap = name == "StudentPOSnapshot"
    head, fill = ("#7a4a00", "#fff5e6") if snap else ("#1d3f7a", "#f6f9ff")
    o.append(f'<rect x="{x}" y="{y}" width="{W}" height="{h(name)}" rx="6" fill="{fill}" stroke="{head}" stroke-width="2"/>')
    o.append(f'<path d="M{x} {y+HH}V{y+6}a6 6 0 0 1 6-6H{x+W-6}a6 6 0 0 1 6 6V{y+HH}z" fill="{head}"/>')
    o.append(f'<text x="{x+W/2}" y="{y+28}" text-anchor="middle" font-size="20" font-weight="bold" fill="#fff">{name}</text>')
    for i, r in enumerate(rows):
        key, rest = r[:2].strip(), r[4:]
        ty = y + HH + 22 + i * RH
        color = {"PK": "#a61b1b", "FK": "#1d5a2b", "UQ": "#6b3fa0", "IX": "#555"}.get(key, "#111")
        if key:
            o.append(f'<text x="{x+10}" y="{ty}" font-size="15" font-weight="bold" fill="{color}">{key}</text>')
        o.append(f'<text x="{x+46}" y="{ty}" font-size="15.5" fill="#111">{rest}</text>')
lx, ly = 630, 1120
o.append(f'<rect x="{lx}" y="{ly}" width="970" height="80" rx="6" fill="#fafafa" stroke="#999" stroke-width="1.5"/>')
o.append(f'<text x="{lx+16}" y="{ly+30}" font-size="17" fill="#111"><tspan font-weight="bold" fill="#a61b1b">PK</tspan> primary key   <tspan font-weight="bold" fill="#1d5a2b">FK</tspan> foreign key   <tspan font-weight="bold" fill="#6b3fa0">UQ</tspan> unique constraint   <tspan font-weight="bold" fill="#555">IX</tspan> extra composite index</text>')
o.append(f'<text x="{lx+16}" y="{ly+60}" font-size="17" fill="#111">Arrow: FK table → referenced table (N → 1).  Orange table: precomputed PO profile.</text>')
o.append("</svg>")
Path(__file__).with_name("er.svg").write_text("\n".join(o), encoding="utf-8")
