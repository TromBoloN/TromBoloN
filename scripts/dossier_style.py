"""Shared visual language for every SVG on the profile.

Industrial machine-panel look: heavy bevelled copper plates with cut corners
and screws, oxblood panels, a dark desk of scattered papers behind it all,
and a condensed display face (Anton, OFL, embedded) with hard outlines.
Text is kept to a minimum: big titles, big numbers, little else.

Rules: no gradients, no blur, no glow. Bevels are flat stepped layers.
Only the Python standard library is used.
"""
from __future__ import annotations

import base64
import math
import os
import random
from html import escape

SUBJECT_ID = "64-TRB-0217"

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------
BG = "#0c0806"
DESK = "#18110d"
DESK_LINE = "#231a14"
COPPER = "#94602f"
COPPER_HI = "#d39a5c"
COPPER_LO = "#5a3519"
COPPER_DK = "#21140b"
OXBLOOD = "#1d0b08"
OXBLOOD_2 = "#2e0f0b"
RED = "#b3261e"
RED_DIM = "#5e1812"
RED_HI = "#e0472f"
AMBER = "#f2b630"
CREAM = "#ecdfc6"
MUTED = "#9b8a74"
OUTLINE = "#120804"

DISPLAY = "Anton,Impact,'Arial Narrow Bold','Arial Narrow',sans-serif"
SANS = "'Segoe UI',Inter,'Helvetica Neue',Helvetica,Arial,sans-serif"

_FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "anton-subset.woff")


def _font_face() -> str:
    try:
        with open(_FONT_PATH, "rb") as handle:
            data = base64.b64encode(handle.read()).decode()
    except OSError:
        return ""  # falls back to Impact & co.
    return f"@font-face{{font-family:'Anton';src:url(data:font/woff;base64,{data}) format('woff')}}"


CSS = f"""{_font_face()}
.d{{font-family:{DISPLAY};text-transform:uppercase}}
.s{{font-family:{SANS}}}
.cr{{shape-rendering:crispEdges}}
.lamp{{animation:lamp 2.6s steps(1) infinite}}
@keyframes lamp{{0%,100%{{opacity:1}}44%{{opacity:.15}}50%{{opacity:1}}56%{{opacity:.15}}62%{{opacity:1}}}}
.blink{{animation:blink 5s steps(1) infinite}}
@keyframes blink{{0%,100%{{transform:scaleY(1)}}96%{{transform:scaleY(.1)}}}}
.in{{animation:in .6s steps(5) backwards}}
@keyframes in{{from{{opacity:0}}to{{opacity:1}}}}
.sweep{{animation:sweep 6s steps(30) infinite}}
@keyframes sweep{{from{{transform:translateY(0)}}to{{transform:translateY(var(--h))}}}}
"""

DEFS = f"""
<filter id="grime" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3" seed="4" stitchTiles="stitch"/>
  <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .7 -.22"/>
</filter>
<filter id="wear" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".05 .9" numOctaves="2" seed="9" stitchTiles="stitch"/>
  <feColorMatrix values="0 0 0 0 .9  0 0 0 0 .75  0 0 0 0 .55  0 0 0 .5 -.3"/>
</filter>
<pattern id="dots" width="4" height="4" patternUnits="userSpaceOnUse">
  <rect x="0" y="0" width="1.4" height="1.4" fill="#000" opacity=".45"/>
</pattern>
"""


def e(text) -> str:
    return escape(str(text))


def doc(width: int, height: int, title: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{e(title)}">'
        f"<title>{e(title)}</title><style>{CSS}</style><defs>{DEFS}</defs>\n"
        f"{body}\n</svg>\n"
    )


def display_width(text: str, size: float) -> float:
    return len(text) * size * 0.47


# --------------------------------------------------------------------------
# Text
# --------------------------------------------------------------------------
def display(x, y, text, size, fill=CREAM, anchor="start", spacing=0.5, extra="") -> str:
    """Condensed display text with a hard outline and a hard drop shadow."""
    common = (
        f'x="{x}" y="{y}" class="d" font-size="{size}" text-anchor="{anchor}" '
        f'letter-spacing="{spacing}" {extra}'
    )
    stroke = max(size * 0.1, 2)
    return (
        f'<text {common} transform="translate(2 3)" fill="#000" opacity=".6" '
        f'stroke="#000" stroke-width="{stroke:.1f}">{e(text)}</text>'
        f'<text {common} fill="{fill}" stroke="{OUTLINE}" stroke-width="{stroke:.1f}" '
        f'stroke-linejoin="miter" paint-order="stroke">{e(text)}</text>'
    )


def small(x, y, text, size=12, fill=MUTED, anchor="start", extra="") -> str:
    return (
        f'<text x="{x}" y="{y}" class="s" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}" {extra}>{e(text)}</text>'
    )


def tag(x, y, text, size=13, fill=RED, color=CREAM) -> str:
    """Slanted red label tag."""
    w = display_width(text, size) + 22
    h = size + 10
    k = h * 0.35
    return (
        f'<polygon points="{x + k:.1f},{y} {x + w + k:.1f},{y} {x + w:.1f},{y + h} {x},{y + h}" '
        f'fill="{fill}" stroke="{OUTLINE}" stroke-width="1.5"/>'
        + f'<text x="{x + w / 2 + k / 2:.1f}" y="{y + h - 6:.1f}" class="d" font-size="{size}" '
        f'fill="{color}" text-anchor="middle" letter-spacing=".6">{e(text)}</text>'
    )


# --------------------------------------------------------------------------
# Plates
# --------------------------------------------------------------------------
def cham(x, y, w, h, c) -> str:
    """Points of a rectangle with all four corners cut."""
    return " ".join(
        f"{px:.1f},{py:.1f}"
        for px, py in (
            (x + c, y), (x + w - c, y), (x + w, y + c), (x + w, y + h - c),
            (x + w - c, y + h), (x + c, y + h), (x, y + h - c), (x, y + c),
        )
    )


def screw(cx, cy, r=4.5, seed=0) -> str:
    angle = random.Random(seed).uniform(0, 180)
    dx, dy = r * 0.7 * math.cos(math.radians(angle)), r * 0.7 * math.sin(math.radians(angle))
    return (
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{COPPER_LO}" stroke="{COPPER_DK}" stroke-width="1.5"/>'
        f'<circle cx="{cx - .8:.1f}" cy="{cy - .8:.1f}" r="{r - 1.6:.1f}" fill="none" stroke="{COPPER_HI}" stroke-width=".8" opacity=".6"/>'
        f'<path d="M{cx - dx:.1f} {cy - dy:.1f}L{cx + dx:.1f} {cy + dy:.1f}" stroke="{COPPER_DK}" stroke-width="1.6"/>'
    )


_ids = iter(range(1, 10_000))


def plate(x, y, w, h, *, c=16, rim=9, fill=OXBLOOD, metal=COPPER, hi=COPPER_HI,
          lo=COPPER_LO, screws=True) -> tuple[str, tuple[float, float, float, float], str]:
    """Bevelled metal frame around a dark panel.

    Returns (svg, inner box (x, y, w, h), clip id of the inner panel).
    """
    cid = f"p{next(_ids)}"
    ix, iy, iw, ih = x + rim, y + rim, w - 2 * rim, h - 2 * rim
    ic = max(c - rim * 0.6, 4)
    out = [
        f'<polygon points="{cham(x + 3, y + 5, w, h, c)}" fill="#000" opacity=".55"/>',  # hard shadow
        f'<polygon points="{cham(x, y, w, h, c)}" fill="{hi}"/>',                         # highlight
        f'<polygon points="{cham(x + 2, y + 2, w - 2, h - 2, c)}" fill="{COPPER_DK}"/>',  # shadow side
        f'<polygon points="{cham(x + 2, y + 2, w - 4, h - 4, c)}" fill="{metal}"/>',      # face
        f'<polygon points="{cham(x + 2, y + 2, w - 4, h - 4, c)}" fill="{metal}" filter="url(#wear)" opacity=".35"/>',
        f'<polygon points="{cham(ix - 2, iy - 2, iw + 4, ih + 4, ic + 1)}" fill="{lo}"/>',   # inner lip
        f'<polygon points="{cham(ix, iy, iw, ih, ic)}" fill="{fill}"/>',
        f'<clipPath id="{cid}"><polygon points="{cham(ix, iy, iw, ih, ic)}"/></clipPath>',
        f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" filter="url(#grime)" clip-path="url(#{cid})"/>',
        f'<polygon points="{cham(ix + 5, iy + 5, iw - 10, ih - 10, max(ic - 4, 3))}" fill="none" stroke="{lo}" stroke-width="1" opacity=".7"/>',
    ]
    if screws:
        for i, (sx, sy) in enumerate(((x + c * .55, y + c * .55), (x + w - c * .55, y + c * .55),
                                      (x + c * .55, y + h - c * .55), (x + w - c * .55, y + h - c * .55))):
            out.append(screw(sx, sy, 3.6, seed=int(x + y) + i))
    return "\n".join(out), (ix, iy, iw, ih), cid


def desk(width: int, height: int, seed: int = 1) -> str:
    """Dark background strewn with old papers. Deliberately low contrast."""
    rng = random.Random(seed)
    out = [f'<rect width="{width}" height="{height}" fill="{BG}"/>']
    for _ in range(7):
        pw, ph = rng.uniform(140, 260), rng.uniform(170, 300)
        px, py = rng.uniform(-80, width - 60), rng.uniform(-120, height - 40)
        rot = rng.uniform(-18, 18)
        lines = "".join(
            f'<rect x="{18}" y="{30 + i * 14}" width="{rng.uniform(40, pw - 40):.0f}" height="3" fill="{DESK_LINE}"/>'
            for i in range(int((ph - 60) / 14))
            if rng.random() < 0.8
        )
        out.append(
            f'<g transform="translate({px:.0f} {py:.0f}) rotate({rot:.1f})">'
            f'<rect width="{pw:.0f}" height="{ph:.0f}" fill="{DESK}" stroke="{DESK_LINE}"/>{lines}</g>'
        )
    out.append(f'<rect width="{width}" height="{height}" filter="url(#grime)"/>')
    return "\n".join(out)


def emblem(cx: float, cy: float, r: float, color=COPPER_HI, eye=RED_HI) -> str:
    """Invented seal: a gear around a watching eye."""
    teeth, pts = 14, []
    for i in range(teeth * 2):
        radius = r if i % 2 == 0 else r * 0.84
        for j in (-0.3, 0.3):
            a = (i + j) * math.pi / teeth
            pts.append(f"{cx + radius * math.cos(a):.1f},{cy + radius * math.sin(a):.1f}")
    lens = " ".join(
        f"{cx + dx * r:.1f},{cy + dy * r:.1f}"
        for dx, dy in ((-.6, 0), (-.25, -.3), (.25, -.3), (.6, 0), (.25, .3), (-.25, .3))
    )
    p = r * 0.14
    return (
        f'<g stroke="{OUTLINE}" stroke-width="2">'
        f'<polygon points="{" ".join(pts)}" fill="{COPPER}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r * .72:.1f}" fill="{COPPER_DK}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r * .72:.1f}" fill="none" stroke="{color}" stroke-width="1.2"/>'
        f'<polygon points="{lens}" fill="{OXBLOOD_2}" stroke="{color}" stroke-width="1.5"/>'
        f'<g class="blink" style="transform-origin:{cx}px {cy}px">'
        f'<rect x="{cx - p:.1f}" y="{cy - p:.1f}" width="{2 * p:.1f}" height="{2 * p:.1f}" fill="{eye}" '
        f'stroke="none" transform="rotate(45 {cx} {cy})"/></g>'
        "</g>"
    )
