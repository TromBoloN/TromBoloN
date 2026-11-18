#!/usr/bin/env python3
"""Render the static dossier SVGs (header, competencies, case files, footer).

Edit PROFILE below, then run:
    python scripts/render_dossier.py
and commit the files it writes to assets/.
The live, data-driven cards come from generate_stats_card.py instead.
"""
from __future__ import annotations

import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dossier_style import (  # noqa: E402
    BLOOD, BRASS, DIM, FADED, FORM, INSTITUTION, LINE, PAPER, SECTOR, SOOT,
    SUBJECT_ID, VOID, barcode, doc, e, emblem, frame, hazard, header_rule,
    label, redact, skyline, smog, smoke, stamp, text_width,
)

PROFILE = {
    "name": "ARIF ABDURRAHMAN SIDDIQ",
    "alias": "TromBoloN",
    "fields": [
        ("ASSIGNMENT", "BACKEND · WEBGIS · FULL-STACK", PAPER),
        ("SECTOR", "KALIMANTAN TIMUR, ID", PAPER),
        ("STATUS", "ACTIVE — UNDER OBSERVATION", BLOOD),
        ("PRIOR AFFILIATION", None, PAPER),  # None = redacted
    ],
    "competencies": [
        ("A", "LANGUAGES", ["Python", "TypeScript", "JavaScript", "PHP", "C++", "HTML5", "CSS3"]),
        ("B", "INTERFACE", ["Next.js", "React", "Vite", "Tailwind CSS", "shadcn/ui", "Bootstrap"]),
        ("C", "INFRASTRUCTURE", ["Django", "FastAPI", "Laravel", "Supabase", "PostgreSQL", "SQLite", "REST API"]),
        ("G", "CARTOGRAPHY & DATA", ["Leaflet", "Turf.js", "GeoPandas", "Pandas", "Chart.js"]),
        ("T", "TOOLING", ["Git", "GitHub", "GitHub Actions", "VS Code"]),
    ],
    "cases": [
        {
            "file": "case-01.svg",
            "no": "CR-64-001",
            "title": "MIT-WEEK 2026 Portal",
            "kind": "WEB DEVELOPMENT COMPETITION PLATFORM",
            "summary": (
                "Official portal for the MIT-WEEK 2026 web development competition. "
                "Teams submit their work; judges score it blind against a weighted rubric; "
                "the committee administers everything from one panel. Once results are "
                "released, scores are sealed at the database level."
            ),
            "role": "AUTHOR",
            "equipment": "NEXT.JS 16 · REACT 19 · TYPESCRIPT · TAILWIND V4 · SUPABASE · POSTGRESQL",
            "status": "ACTIVE",
        },
        {
            "file": "case-02.svg",
            "no": "CR-64-002",
            "title": "Pemesanan Makanan Digital",
            "kind": "DIGITAL FOOD ORDERING SYSTEM",
            "summary": (
                "Orders placed by scanning a QR code at the table. A cashier panel. "
                "A rule-based recommendation chatbot that speaks Indonesian."
            ),
            "role": "DATABASE DESIGN · ENTIRE DJANGO BACKEND",
            "equipment": "DJANGO · PYTHON · REST API",
            "status": "FILED",
        },
        {
            "file": "case-03.svg",
            "no": "CR-64-003",
            "title": "WebGIS Kaltim",
            "kind": "POWER PLANT MAP OF KALIMANTAN",
            "summary": (
                "Leaflet map of regional power plants with a renewable-share choropleth, "
                "search, filters and CSV export."
            ),
            "role": "TEAM MEMBER · GREEN HOSA, UNIV. MULAWARMAN",
            "equipment": "REACT · FASTAPI · POSTGRESQL · LEAFLET",
            "status": "FILED",
        },
    ],
}

W = 860


# --------------------------------------------------------------------------
def render_header() -> str:
    h = 372
    out = [frame(W, h)]

    # Letterhead
    out.append(emblem(46, 42, 18))
    out.append(f'<text x="76" y="40" class="se" font-size="16" fill="{PAPER}" letter-spacing="3">{e(INSTITUTION)}</text>')
    out.append(label(76, 56, f"{SECTOR} · PERSONNEL ARCHIVE · DEPT. OF CONTINUITY", 10))
    out.append(label(W - 28, 36, FORM, 10, FADED, "end"))
    out.append(
        f'<rect class="cr" x="{W - 196}" y="44.5" width="168" height="16" fill="none" stroke="{BLOOD}"/>'
        + label(W - 112, 56, "CLASSIFICATION: RESTRICTED", 9.5, BLOOD, "middle")
    )
    out.append(f'<path class="cr" d="M20 72.5H{W - 20}M20 75.5H{W - 20}" stroke="{LINE}"/>')

    # File tab
    out.append(
        f'<path class="cr" d="M28 96V84H48L54 78H300V96Z" fill="{SOOT}" stroke="{LINE}"/>'
        + label(60, 91, f"PERSONNEL FILE · SUBJ {SUBJECT_ID}", 9.5, FADED)
    )

    # Subject block
    out.append(label(32, 122, "SUBJECT", 9.5))
    out.append(f'<text x="30" y="160" class="se" font-size="38" fill="{PAPER}">{e(PROFILE["name"])}</text>')
    alias = f"ALIAS: {PROFILE['alias'].upper()}"
    out.append(
        '<clipPath id="tw"><rect x="30" y="170" width="0" height="20">'
        f'<animate attributeName="width" values="{";".join([str(i * 8) for i in range(len(alias) + 1)] + ["420"])}" '
        f'dur="{len(alias) * 0.07:.2f}s" begin=".4s" fill="freeze" calcMode="discrete"/></rect></clipPath>'
        f'<text x="32" y="184" class="mo" font-size="13" fill="{BRASS}" clip-path="url(#tw)">{e(alias)}</text>'
    )

    # Fields
    y = 214
    for i, (name, value, color) in enumerate(PROFILE["fields"]):
        col, row = i % 2, i // 2
        fx, fy = 32 + col * 300, y + row * 32
        out.append(label(fx, fy, name, 9))
        if value is None:
            out.append(redact(fx, fy + 6, 150, 12))
        else:
            out.append(label(fx, fy + 16, value, 12, color))
        out.append(f'<path class="cr" d="M{fx} {fy + 22.5}H{fx + 270}" stroke="{LINE}" stroke-dasharray="1 3"/>')

    # Photograph withheld
    px, py, pw, ph = W - 196, 90, 168, 150
    out.append(f'<rect class="cr" x="{px + .5}" y="{py + .5}" width="{pw}" height="{ph}" fill="url(#hatch)" stroke="{LINE}"/>')
    out.append(f'<rect class="cr" x="{px + 24}" y="{py + 60}" width="{pw - 48}" height="30" fill="{VOID}"/>')
    out.append(label(px + pw / 2, py + 79, "PHOTOGRAPH WITHHELD", 9.5, FADED, "middle"))
    out.append(label(px + 8, py + 16, "FIG. 1", 9, DIM))
    out.append(label(px + pw - 8, py + ph - 8, "REF 0217", 9, DIM, "end"))
    out.append(barcode(SUBJECT_ID, px, py + ph + 10, pw, 22))
    out.append(label(px + pw / 2, py + ph + 44, SUBJECT_ID, 9, FADED, "middle"))

    out.append(stamp("RETAINED", 562, 198, -9, 26, BLOOD, "BY ORDER OF THE ARCHIVE"))

    # Skyline band
    base = h - 22
    out.append(smog(10, base - 64, W - 20, 64))
    back, _ = skyline(11, 10, W - 10, base, 70, "#2a221d")
    front, stacks = skyline(29, 10, W - 10, base, 58, VOID, lights=True)
    out.append(f'<svg x="6" y="0" width="{W - 12}" height="{h}" overflow="hidden">'
               f'{back}{smoke(stacks)}{front}')
    if stacks:
        lx, ly = min(stacks, key=lambda s: s[1])
        out.append(f'<rect class="lamp cr" x="{lx - 2:.0f}" y="{ly - 3:.0f}" width="4" height="4" fill="{BLOOD}"/>')
    out.append("</svg>")
    out.append(hazard(6, base, W - 12, 10))
    out.append(
        f'<rect class="cr" x="18" y="{base - 18}" width="232" height="13" fill="{VOID}"/>'
        + label(22, base - 8, "SURVEILLANCE GRID 64-E · FEED", 9, DIM)
        + redact(196, base - 16, 50, 9)
    )
    return doc(W, h, f"Personnel file: {PROFILE['name'].title()} ({PROFILE['alias']})", "\n".join(out))


# --------------------------------------------------------------------------
def render_competencies() -> str:
    rows = PROFILE["competencies"]
    chip_h, gap, area_x, area_w = 22, 8, 230, W - 230 - 30
    layout, y = [], 72
    for cls, name, items in rows:
        cx, cy, chips = area_x, y, []
        for i, item in enumerate(items, 1):
            code = f"{cls}-{i:02d}"
            cw = text_width(item.upper(), 11) + text_width(code, 9) + 26
            if cx + cw > area_x + area_w:
                cx, cy = area_x, cy + chip_h + 6
            chips.append((cx, cy, cw, item, code))
            cx += cw + gap
        row_h = (cy - y) + chip_h + 18
        layout.append((cls, name, y, row_h, chips))
        y += row_h
    h = y + 34
    out = [frame(W, h), header_rule(28, 42, W - 56, "II", "CERTIFIED COMPETENCIES", "REF/CR-64-02")]
    for cls, name, ry, rh, chips in layout:
        out.append(f'<text x="34" y="{ry + 20}" class="st" font-size="22" fill="{BLOOD}" filter="url(#rough)">{e(cls)}</text>')
        out.append(label(62, ry + 11, f"CLASS {cls}", 9, FADED))
        out.append(label(62, ry + 25, name, 11.5, PAPER, extra='font-weight="700"'))
        for cx, cy, cw, item, code in chips:
            out.append(
                f'<rect class="cr" x="{cx + .5:.1f}" y="{cy + .5}" width="{cw:.1f}" height="{chip_h}" fill="{SOOT}" stroke="{LINE}"/>'
                + label(f"{cx + 8:.1f}", cy + 15, item, 11, PAPER)
                + label(f"{cx + cw - 7:.1f}", cy + 15, code, 9, FADED, "end")
            )
        out.append(f'<path class="cr" d="M28 {ry + rh - 8.5}H{W - 28}" stroke="{SOOT}"/>')
    out.append(label(28, h - 18, "COMPETENCIES SELF-DECLARED · NOT INDEPENDENTLY VERIFIED", 9, DIM))
    out.append(label(W - 28, h - 18, f"{sum(len(r[2]) for r in rows)} ENTRIES", 9, DIM, "end"))
    return doc(W, h, "Certified competencies: " + "; ".join(f"{n}: {', '.join(i)}" for _, n, i in rows), "\n".join(out))


# --------------------------------------------------------------------------
def render_case(case: dict, width: int, height: int) -> str:
    out = [frame(width, height)]
    out.append(label(24, 32, f"CASE FILE № {case['no']}", 10, FADED))
    out.append(label(width - 24, 32, f"{SECTOR} · {FORM}", 9, DIM, "end"))
    out.append(f'<path class="cr" d="M20 40.5H{width - 20}" stroke="{LINE}"/>')
    out.append(f'<text x="22" y="74" class="se" font-size="{26 if width > 600 else 20}" fill="{PAPER}">{e(case["title"])}</text>')
    out.append(label(24, 94, case["kind"], 10, BRASS))

    chars = int((width - 48) / 7.3)
    y = 120
    for line in textwrap.wrap(case["summary"], chars):
        out.append(f'<text x="24" y="{y}" class="ty" font-size="12.5" fill="{PAPER}" opacity=".9">{e(line)}</text>')
        y += 17
    y += 8
    for key, value in (("ROLE OF SUBJECT", case["role"]), ("EQUIPMENT", case["equipment"])):
        out.append(label(24, y, key, 9))
        vy = y + 15
        for line in textwrap.wrap(value, int((width - 48) / 6.7)):
            out.append(label(24, vy, line, 11, PAPER))
            vy += 15
        y = vy + 8

    foot = height - 22
    out.append(f'<path class="cr" d="M20 {foot - 16.5}H{width - 20}" stroke="{LINE}"/>')
    out.append(label(24, foot, "OPEN FILE ▸", 10.5, BRASS, extra='font-weight="700"'))
    out.append(barcode(case["no"], width - 24 - 110, foot - 11, 110, 13, FADED))
    color = BLOOD if case["status"] == "ACTIVE" else FADED
    if width > 600:
        out.append(stamp(case["status"], width - 90, 78, -7, 24, color))
    else:
        out.append(stamp(case["status"], width - 62, 64, -7, 17, color))
    return doc(width, height, f"Case file {case['no']}: {case['title']}. {case['summary']}", "\n".join(out))


def case_height(case: dict, width: int) -> int:
    lines = len(textwrap.wrap(case["summary"], int((width - 48) / 7.3)))
    meta = sum(len(textwrap.wrap(v, int((width - 48) / 6.7))) for v in (case["role"], case["equipment"]))
    return 120 + lines * 17 + 8 + 2 * (15 + 8) + meta * 15 + 40


# --------------------------------------------------------------------------
def render_footer() -> str:
    h = 84
    out = [frame(W, h), hazard(6, 6, W - 12, 9), hazard(6, h - 15, W - 12, 9)]
    out.append(f'<text x="{W / 2}" y="46" class="st" font-size="22" fill="{PAPER}" text-anchor="middle" filter="url(#rough)">END OF RECORD</text>')
    out.append(label(W / 2, 62, f"UNAUTHORIZED REPRODUCTION WILL BE NOTED · {FORM} · PAGE 1 OF 1", 9.5, FADED, "middle"))
    out.append(emblem(40, 42, 13, DIM) + emblem(W - 40, 42, 13, DIM))
    return doc(W, h, "End of record", "\n".join(out))


# --------------------------------------------------------------------------
def main() -> None:
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
    out_dir = sys.argv[1] if len(sys.argv) > 1 else root
    os.makedirs(out_dir, exist_ok=True)

    files = {
        "dossier-header.svg": render_header(),
        "competencies.svg": render_competencies(),
        "end-of-record.svg": render_footer(),
    }
    first, *rest = PROFILE["cases"]
    files[first["file"]] = render_case(first, W, case_height(first, W))
    half = 420
    pair_h = max(case_height(c, half) for c in rest)
    for case in rest:
        files[case["file"]] = render_case(case, half, pair_h)

    for name, content in files.items():
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        print(f"Wrote {os.path.normpath(path)}")


if __name__ == "__main__":
    main()
