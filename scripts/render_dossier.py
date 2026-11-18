#!/usr/bin/env python3
"""Render the static profile SVGs: the header plate and one plate per project.

Edit PROFILE below, then run:
    python scripts/render_dossier.py
and commit what it writes to assets/.
The live activity panel comes from generate_stats_card.py instead.
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dossier_style import (  # noqa: E402
    AMBER, COPPER_HI, COPPER_LO, CREAM, MUTED, OXBLOOD, OXBLOOD_2, RED,
    RED_DIM, RED_HI, SUBJECT_ID, desk, display, display_width, doc, emblem,
    plate, small, tag,
)

PROFILE = {
    "name": "ARIF ABDURRAHMAN SIDDIQ",
    "alias": "TROMBOLON",
    "region": "KALIMANTAN TIMUR",
    "line": "Backend developer. Usually builds for the web.",
    "cases": [
        {"file": "case-01.svg", "no": "01", "title": ["MIT-WEEK", "PORTAL"], "art": "podium", "active": True,
         "alt": "MIT-WEEK 2026 Portal: web development competition platform (Next.js, Supabase)."},
        {"file": "case-02.svg", "no": "02", "title": ["PEMESANAN", "MAKANAN"], "art": "qr", "active": False,
         "alt": "Pemesanan Makanan Digital: QR-code food ordering system (Django backend)."},
        {"file": "case-03.svg", "no": "03", "title": ["WEBGIS", "KALTIM"], "art": "map", "active": False,
         "alt": "WebGIS Kaltim: power plant map of Kalimantan (React, FastAPI, Leaflet)."},
    ],
}

W = 860


# --------------------------------------------------------------------------
def render_header() -> str:
    h = 250
    out = [desk(W, h, seed=3)]

    # Main ID plate
    svg, (ix, iy, iw, ih), _ = plate(14, 14, 576, h - 30)
    out.append(svg)
    out.append(display(ix + 22, iy + 30, f"NO. {SUBJECT_ID}", 14, MUTED, spacing=1.2, extra='font-style="italic"'))
    out.append(display(ix + 20, iy + 100, PROFILE["name"], 50, CREAM, spacing=0.8))
    out.append(display(ix + 22, iy + 142, PROFILE["alias"], 30, AMBER, spacing=2))
    out.append(tag(ix + 44 + display_width(PROFILE["alias"], 30) + 2 * len(PROFILE["alias"]), iy + 117, PROFILE["region"], 14))
    out.append(f'<rect class="cr" x="{ix + 22}" y="{iy + 158}" width="{iw - 44}" height="2" fill="{COPPER_LO}"/>')
    out.append(small(ix + 22, iy + 184, PROFILE["line"], 15, CREAM, extra='opacity=".85"'))

    # Seal plate
    svg, (sx, sy, sw, sh), _ = plate(606, 14, 240, h - 30, metal="#7a2a1c", hi="#c0573b", lo="#3d120c", fill=OXBLOOD_2)
    out.append(svg)
    cx = sx + sw / 2
    out.append(emblem(cx, sy + 78, 56))
    out.append(f'<rect class="cr" x="{sx + 26}" y="{sy + sh - 52}" width="{sw - 52}" height="32" fill="{OXBLOOD}" stroke="{COPPER_LO}" stroke-width="2"/>')
    out.append(f'<rect class="lamp cr" x="{sx + 38}" y="{sy + sh - 40}" width="9" height="9" fill="{RED_HI}"/>')
    out.append(display(cx + 8, sy + sh - 27, "ACTIVE", 18, AMBER, "middle", spacing=2))
    return doc(W, h, f"{PROFILE['name'].title()} ({PROFILE['alias']}): {PROFILE['line']} {PROFILE['region'].title()}.", "\n".join(out))


# --------------------------------------------------------------------------
def art_podium(x, y, w, h) -> str:
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#1a0f08"/>']
    for i, dx in enumerate((-0.28, 0, 0.28)):  # spotlight beams, flat polygons
        bx = x + w / 2 + dx * w
        out.append(
            f'<polygon points="{bx - 6:.0f},{y} {bx + 6:.0f},{y} {bx + 40:.0f},{y + h} {bx - 40:.0f},{y + h}" '
            f'fill="{AMBER}" opacity="{.10 if i != 1 else .18}"/>'
        )
    base = y + h - 8
    for dx, ph, label in ((-58, 34, "2"), (0, 54, "1"), (58, 22, "3")):
        px = x + w / 2 + dx - 26
        out.append(f'<rect class="cr" x="{px:.0f}" y="{base - ph}" width="52" height="{ph}" fill="#3a2414" stroke="#120804" stroke-width="2"/>')
        out.append(display(px + 26, base - ph + 22, label, 18, AMBER if label == "1" else MUTED, "middle"))
    out.append(f'<rect class="cr" x="{x}" y="{base}" width="{w}" height="8" fill="#120804"/>')
    return "".join(out)


def art_qr(x, y, w, h) -> str:
    rng = random.Random(64)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#1c0c08"/>']
    n, cell = 21, (h - 20) / 21
    ox, oy = x + w / 2 - n * cell / 2, y + 10
    out.append(f'<rect class="cr" x="{ox - 6:.0f}" y="{oy - 6:.0f}" width="{n * cell + 12:.0f}" height="{n * cell + 12:.0f}" fill="#d9c9a8"/>')
    cells = []
    for r in range(n):
        for c in range(n):
            finder = any(r0 <= r < r0 + 7 and c0 <= c < c0 + 7 for r0, c0 in ((0, 0), (0, n - 7), (n - 7, 0)))
            if finder:
                rr, cc = r % 7 if r < 7 else (r - (n - 7)), c % 7 if c < 7 else (c - (n - 7))
                on = rr in (0, 6) or cc in (0, 6) or (2 <= rr <= 4 and 2 <= cc <= 4)
            else:
                on = rng.random() < 0.48
            if on:
                cells.append(f'<rect x="{ox + c * cell:.1f}" y="{oy + r * cell:.1f}" width="{cell + .3:.1f}" height="{cell + .3:.1f}"/>')
    out.append(f'<g class="cr" fill="#1a0d07">{"".join(cells)}</g>')
    # scan line
    out.append(f'<rect class="sweep cr" style="--h:{n * cell:.0f}px" x="{ox - 10:.0f}" y="{oy}" width="{n * cell + 20:.0f}" height="2" fill="{RED_HI}"/>')
    return "".join(out)


def art_map(x, y, w, h) -> str:
    rng = random.Random(14)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#2a0806"/>']
    cx, cy = x + w / 2, y + h / 2
    import math

    for ring in (0.18, 0.38, 0.6, 0.85, 1.15):
        pts = []
        for k in range(9):
            a = k * 2 * math.pi / 9 + ring
            rad = ring * h * rng.uniform(0.85, 1.15)
            pts.append(f"{cx + rad * math.cos(a) * 1.4:.0f},{cy + rad * math.sin(a):.0f}")
        out.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="{RED}" stroke-width="1.2" opacity=".75"/>')
    for k in range(9):
        a = k * 2 * math.pi / 9 + 0.3
        out.append(f'<path d="M{cx + 12 * math.cos(a):.0f} {cy + 12 * math.sin(a):.0f}L{cx + 200 * math.cos(a):.0f} {cy + 140 * math.sin(a):.0f}" stroke="{RED_DIM}" stroke-width="1"/>')
    for k, (px, py) in enumerate(((-0.28, -0.22), (0.18, -0.3), (0.05, 0.12), (0.32, 0.2), (-0.2, 0.3))):
        mx, my = cx + px * w, cy + py * h
        cls = ' class="lamp"' if k == 2 else ""
        out.append(f'<rect{cls} x="{mx - 4:.0f}" y="{my - 4:.0f}" width="8" height="8" fill="{RED_HI}" stroke="#120804" stroke-width="1.5" transform="rotate(45 {mx:.0f} {my:.0f})"/>')
    return "".join(out)


ARTS = {"podium": art_podium, "qr": art_qr, "map": art_map}


def render_case(case: dict) -> str:
    w, h = 284, 236
    out = [desk(w, h, seed=int(case["no"]) + 10)]
    accent = dict(metal="#a07a22", hi="#f2c45a", lo="#5a4310") if case["active"] else {}
    svg, (ix, iy, iw, ih), cid = plate(8, 8, w - 18, h - 20, **accent)
    out.append(svg)
    art_h = ih - 78
    out.append(f'<clipPath id="art"><rect x="{ix}" y="{iy}" width="{iw}" height="{art_h}"/></clipPath>'
               f'<g clip-path="url(#{cid})"><g clip-path="url(#art)">{ARTS[case["art"]](ix, iy, iw, art_h)}'
               f'<rect x="{ix}" y="{iy}" width="{iw}" height="{art_h}" fill="url(#dots)"/></g></g>')
    out.append(f'<rect class="cr" x="{ix}" y="{iy + art_h}" width="{iw}" height="3" fill="{COPPER_HI}" opacity=".7"/>')
    t1, t2 = case["title"]
    out.append(display(ix + iw / 2, iy + art_h + 36, t1, 28, AMBER if case["active"] else CREAM, "middle", 1))
    out.append(display(ix + iw / 2, iy + art_h + 66, t2, 22, AMBER if case["active"] else CREAM, "middle", 1.5))
    out.append(tag(ix + 8, iy + 10, case["no"], 14, RED))
    return doc(w, h, case["alt"], "\n".join(out))


# --------------------------------------------------------------------------
def main() -> None:
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
    out_dir = sys.argv[1] if len(sys.argv) > 1 else root
    os.makedirs(out_dir, exist_ok=True)
    files = {"dossier-header.svg": render_header()}
    for case in PROFILE["cases"]:
        files[case["file"]] = render_case(case)
    for name, content in files.items():
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        print(f"Wrote {os.path.normpath(path)}")


if __name__ == "__main__":
    main()
