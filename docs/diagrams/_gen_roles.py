"""Rol akış şemasını (roles.svg) üretir:  python docs/diagrams/_gen_roles.py"""
from pathlib import Path

LW, GAP, X0 = 355, 25, 30
LANES = [
    ("Admin", "System Administrator", "#4a5866", "#eef1f4",
     ["User accounts", "Roles and permission groups"],
     ["All records (Django admin)"]),
    ("Department Head", "DEPT_HEAD", "#7a4a00", "#fff5e6",
     ["11 Program Outcomes (PO)", "Courses and term", "Instructor assignment", "Student enrollment"],
     ["LOs and mappings of all courses", "PO scores of all students", "Department average per PO"]),
    ("Instructor", "INSTRUCTOR", "#1d5a2b", "#f0f9f1",
     ["Course LOs", "Assessments (Midterm…)", "Assessment → LO percentages", "LO → PO weights (1–5)", "Student grades"],
     ["Courses and student lists", "Entered grades", "Students' PO scores"]),
    ("Student", "STUDENT", "#1d3f7a", "#eef4ff",
     ["— (enters no data)"],
     ["Own grades", "Own 11-PO profile", "PO without data: “no data”", "(student dashboard: next sprint)"]),
]
W = X0 * 2 + 4 * LW + 3 * GAP
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 900" font-family="Helvetica, Arial, sans-serif">',
     '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="#333"/></marker></defs>',
     f'<rect width="{W}" height="900" fill="#fff"/>',
     f'<text x="{W/2}" y="42" text-anchor="middle" font-size="28" font-weight="bold" fill="#111">Waffle 5.1 — Roles: Who Enters What, Who Sees What</text>']


def box(x, y, w, hgt, title, items, stroke):
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{hgt}" rx="8" fill="#fff" stroke="{stroke}" stroke-width="1.8"/>')
    o.append(f'<text x="{x+14}" y="{y+30}" font-size="17" font-weight="bold" fill="{stroke}">{title}</text>')
    for i, it in enumerate(items):
        bullet = "" if it.startswith(("—", "(")) else "• "
        o.append(f'<text x="{x+14}" y="{y+62+i*30}" font-size="17.5" fill="#111">{bullet}{it}</text>')


for i, (name, sub, stroke, fill, enters, sees) in enumerate(LANES):
    x = X0 + i * (LW + GAP)
    o.append(f'<rect x="{x}" y="70" width="{LW}" height="800" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>')
    o.append(f'<text x="{x+LW/2}" y="108" text-anchor="middle" font-size="24" font-weight="bold" fill="{stroke}">{name}</text>')
    o.append(f'<text x="{x+LW/2}" y="134" text-anchor="middle" font-size="16" fill="#333">{sub}</text>')
    box(x + 15, 155, LW - 30, 215, "ENTERS", enters, stroke)
    box(x + 15, 630, LW - 30, 220, "SEES", sees, stroke)
    cx = x + LW / 2
    if i < 3:
        o.append(f'<line x1="{cx}" y1="370" x2="{cx}" y2="428" stroke="#333" stroke-width="2.2" marker-end="url(#a)"/>')
    o.append(f'<line x1="{cx}" y1="570" x2="{cx}" y2="628" stroke="#333" stroke-width="2.2" marker-end="url(#a)"/>')
    if i < 2:
        o.append(f'<line x1="{x+LW-15}" y1="262" x2="{x+LW+GAP+13}" y2="262" stroke="#333" stroke-width="2.2" marker-end="url(#a)"/>')

o.append(f'<rect x="{X0+15}" y="430" width="{W-2*X0-30}" height="140" rx="10" fill="#fff" stroke="#a61b1b" stroke-width="2.5"/>')
o.append(f'<text x="{W/2}" y="468" text-anchor="middle" font-size="22" font-weight="bold" fill="#a61b1b">System — automatic recalculation</text>')
o.append(f'<text x="{W/2}" y="503" text-anchor="middle" font-size="18" fill="#111">When a grade, mapping or weight changes, signals → POCalculatorService recalculates only the affected students</text>')
o.append(f'<text x="{W/2}" y="535" text-anchor="middle" font-size="18" fill="#111">Grade → LO → PO:  score = Σ(weight × score) ÷ Σ weight   →   StudentPOSnapshot (student × PO; NULL if no data)</text>')
o.append("</svg>")
Path(__file__).with_name("roles.svg").write_text("\n".join(o), encoding="utf-8")
