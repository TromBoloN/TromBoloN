"""Shared visual language for every SVG on the profile.

The look: an archived personnel record from an industrial, bureaucratic city.
Rules this module enforces on purpose:
  * no gradients, no blur, no glow, no rounded corners
  * 1px solid strokes, sharp corners, hard geometry
  * stencil/stamp lettering only for stamps and section numerals;
    everything technical is uppercase monospace with tight tracking
Only the Python standard library is used.
"""
from __future__ import annotations

import random
from html import escape

# --------------------------------------------------------------------------
# Identity (rename the institution here and every asset follows)
# --------------------------------------------------------------------------
INSTITUTION = "DIRECTORATE OF CIVIC RECORDS"
SECTOR = "SECTOR 64"
FORM = "FORM CR-64/7"
SUBJECT_ID = "64-TRB-0217"

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------
INK = "#16120f"      # card background, charcoal-brown
SOOT = "#221c18"     # panels
LINE = "#4a3f37"     # etched rules
DIM = "#5e554b"      # secondary rules / empty marks
FADED = "#8c8273"    # labels
PAPER = "#d9cfbd"    # primary text
BRASS = "#9c7b4a"    # alias, links, lit windows
OCHRE = "#7d6230"    # caution tape
RUST = "#7a2e24"     # stamps, warnings
BLOOD = "#a3382c"    # accent
VOID = "#070504"     # redaction bars, front skyline

SERIF = "Georgia,'Times New Roman',Times,serif"
MONO = "Consolas,'Liberation Mono','Courier New',monospace"
TYPE = "'Courier New',Courier,'Liberation Mono',monospace"
STENCIL = "Impact,Haettenschweiler,'Arial Narrow Bold','Franklin Gothic Bold','Arial Black',sans-serif"

CSS = f"""
.se{{font-family:{SERIF}}}
.mo{{font-family:{MONO};text-transform:uppercase;letter-spacing:.02em}}
.ty{{font-family:{TYPE}}}
.st{{font-family:{STENCIL};text-transform:uppercase;letter-spacing:.04em}}
.cr{{shape-rendering:crispEdges}}
.thud{{animation:thud .32s cubic-bezier(.2,.9,.3,1) 1.1s both;transform-box:fill-box;transform-origin:center}}
@keyframes thud{{0%{{opacity:0;transform:scale(1.9)}}75%{{opacity:.92;transform:scale(.97)}}100%{{opacity:.88;transform:scale(1)}}}}
.lamp{{animation:lamp 2.8s steps(1) infinite}}
@keyframes lamp{{0%,100%{{opacity:1}}46%{{opacity:.12}}50%{{opacity:1}}55%{{opacity:.12}}58%{{opacity:1}}}}
.win{{animation:win 7.3s steps(1) infinite}}
@keyframes win{{0%,100%{{opacity:.75}}61%{{opacity:.1}}64%{{opacity:.75}}83%{{opacity:.1}}84%{{opacity:.75}}}}
.smoke{{animation:smoke 10s steps(10) infinite}}
@keyframes smoke{{0%{{transform:translate(0,0);opacity:0}}10%{{opacity:.5}}100%{{transform:translate(34px,-64px);opacity:0}}}}
.rise{{animation:rise .5s steps(4) backwards}}
@keyframes rise{{from{{opacity:0}}to{{opacity:1}}}}
"""

DEFS = f"""
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="7" stitchTiles="stitch"/>
  <feColorMatrix values="0 0 0 0 .85  0 0 0 0 .8  0 0 0 0 .72  0 0 0 .17 -.05"/>
</filter>
<filter id="rough" x="-8%" y="-8%" width="116%" height="116%">
  <feTurbulence type="fractalNoise" baseFrequency=".75" numOctaves="2" seed="3" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="2.4" xChannelSelector="R" yChannelSelector="G" result="d"/>
  <feColorMatrix in="n" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -3 2.55" result="wear"/>
  <feComposite in="d" in2="wear" operator="in"/>
</filter>
<pattern id="haz" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="7" height="14" fill="{OCHRE}"/><rect x="7" width="7" height="14" fill="{VOID}"/>
</pattern>
<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="6" height="6" fill="{SOOT}"/><rect width="1" height="6" fill="{LINE}"/>
</pattern>
"""


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def e(text) -> str:
    return escape(str(text))


def text_width(text: str, size: float, factor: float = 0.6) -> float:
    """Rough width of monospace/stencil text, for layout only."""
    return len(text) * size * factor


def doc(width: int, height: int, title: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{e(title)}">'
        f"<title>{e(title)}</title><style>{CSS}</style><defs>{DEFS}</defs>\n"
        f"{body}\n</svg>\n"
    )


def frame(width: int, height: int) -> str:
    """Card background: flat ink, flat grain, double etched rule, corner brackets."""
    w, h = width, height
    out = [
        f'<rect width="{w}" height="{h}" fill="{INK}"/>',
        f'<rect width="{w}" height="{h}" filter="url(#grain)"/>',
        f'<rect class="cr" x=".5" y=".5" width="{w - 1}" height="{h - 1}" fill="none" stroke="{LINE}"/>',
        f'<rect class="cr" x="5.5" y="5.5" width="{w - 11}" height="{h - 11}" fill="none" stroke="{SOOT}"/>',
    ]
    k = 14
    for cx, cy, dx, dy in ((3, 3, 1, 1), (w - 3, 3, -1, 1), (3, h - 3, 1, -1), (w - 3, h - 3, -1, -1)):
        out.append(
            f'<path class="cr" d="M{cx} {cy + dy * k}V{cy}H{cx + dx * k}" '
            f'fill="none" stroke="{PAPER}" stroke-width="2"/>'
        )
    return "\n".join(out)


def label(x, y, text, size=10, fill=FADED, anchor="start", extra="") -> str:
    return (
        f'<text x="{x}" y="{y}" class="mo" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}" {extra}>{e(text)}</text>'
    )


def header_rule(x: float, y: float, width: float, numeral: str, title: str, code: str) -> str:
    """`§ IV  ACTIVITY LEDGER ──────────── REF/CR-64-04`"""
    num = f"§ {numeral}"
    num_w = text_width(num, 20, 0.5)
    title_x = x + num_w + 12
    title_w = text_width(title, 12)
    code_w = text_width(code, 10)
    line_from = title_x + title_w + 12
    line_to = x + width - code_w - 12
    return "\n".join(
        [
            f'<text x="{x}" y="{y}" class="st" font-size="20" fill="{BLOOD}" filter="url(#rough)">{e(num)}</text>',
            f'<text x="{title_x:.1f}" y="{y - 2}" class="mo" font-size="12" font-weight="700" fill="{PAPER}">{e(title)}</text>',
            f'<path class="cr" d="M{line_from:.1f} {y - 6.5}H{line_to:.1f}" stroke="{LINE}"/>',
            label(x + width, y - 2, code, 10, FADED, "end"),
            f'<path class="cr" d="M{x} {y + 8.5}H{x + width}" stroke="{LINE}"/>',
        ]
    )


def redact(x, y, width, height=11) -> str:
    return f'<rect class="cr" x="{x}" y="{y}" width="{width}" height="{height}" fill="{VOID}"/>'


def hazard(x, y, width, height) -> str:
    return (
        f'<rect class="cr" x="{x}" y="{y}" width="{width}" height="{height}" fill="url(#haz)"/>'
        f'<path class="cr" d="M{x} {y + .5}H{x + width}M{x} {y + height - .5}H{x + width}" stroke="{VOID}"/>'
    )


def barcode(seed: str, x: float, y: float, width: float, height: float, fill=PAPER) -> str:
    rng = random.Random(seed)
    out, cursor = [], x
    while cursor < x + width - 3:
        bar = rng.choice((1, 1, 1, 2, 2, 3))
        if cursor + bar > x + width:
            break
        out.append(f'<rect x="{cursor:.0f}" y="{y}" width="{bar}" height="{height}"/>')
        cursor += bar + rng.choice((1, 1, 2, 3))
    return f'<g class="cr" fill="{fill}" opacity=".8">{"".join(out)}</g>'


def stamp(text: str, x: float, y: float, rotate: float = -8, size: float = 24,
          color: str = BLOOD, sub: str | None = None, animate: bool = True) -> str:
    """Double-bordered, roughened ink stamp centred on (x, y)."""
    w = text_width(text, size, 0.52) + 28
    h = size + (16 if sub else 12)
    if sub:
        w = max(w, text_width(sub, 9) + 28)
    left, top = -w / 2, -h / 2
    inner = [
        f'<rect x="{left:.1f}" y="{top:.1f}" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="{color}" stroke-width="2.5"/>',
        f'<rect x="{left + 4:.1f}" y="{top + 4:.1f}" width="{w - 8:.1f}" height="{h - 8:.1f}" fill="none" stroke="{color}" stroke-width="1"/>',
        f'<text x="0" y="{(size * 0.36) - (5 if sub else 0):.1f}" class="st" font-size="{size}" '
        f'fill="{color}" text-anchor="middle">{e(text)}</text>',
    ]
    if sub:
        inner.append(
            f'<text x="0" y="{h / 2 - 8:.1f}" class="mo" font-size="9" fill="{color}" '
            f'text-anchor="middle">{e(sub)}</text>'
        )
    cls = ' class="thud"' if animate else ' opacity=".88"'
    return (
        f'<g transform="translate({x} {y}) rotate({rotate})" filter="url(#rough)">'
        f"<g{cls}>{''.join(inner)}</g></g>"
    )


def emblem(cx: float, cy: float, r: float = 17, color=PAPER) -> str:
    """Invented seal: a hard-edged gear around a watching lens."""
    import math

    teeth, pts = 12, []
    for i in range(teeth * 2):
        radius = r if i % 2 == 0 else r * 0.8
        for j in (-0.32, 0.32):
            angle = (i + j) * math.pi / teeth
            pts.append(f"{cx + radius * math.cos(angle):.1f},{cy + radius * math.sin(angle):.1f}")
    lens = " ".join(
        f"{cx + dx:.1f},{cy + dy:.1f}"
        for dx, dy in ((-r * .55, 0), (-r * .22, -r * .28), (r * .22, -r * .28), (r * .55, 0), (r * .22, r * .28), (-r * .22, r * .28))
    )
    p = r * 0.13
    return (
        f'<g fill="none" stroke="{color}" stroke-width="1">'
        f'<polygon points="{" ".join(pts)}"/>'
        f'<rect x="{cx - r * .62:.1f}" y="{cy - r * .62:.1f}" width="{r * 1.24:.1f}" height="{r * 1.24:.1f}" transform="rotate(45 {cx} {cy})" stroke="{LINE}"/>'
        f'<polygon points="{lens}"/>'
        f'<rect x="{cx - p:.1f}" y="{cy - p:.1f}" width="{2 * p:.1f}" height="{2 * p:.1f}" fill="{BLOOD}" stroke="none" transform="rotate(45 {cx} {cy})"/>'
        "</g>"
    )


# --------------------------------------------------------------------------
# Industrial skyline
# --------------------------------------------------------------------------
def skyline(seed: int, x0: float, x1: float, base: float, max_h: float,
            fill: str, lights: bool = False) -> tuple[str, list[tuple[float, float]]]:
    """Procedural silhouette of stacks, blocks, tanks and gantries.

    Returns the SVG and the (x, y) tops of smokestacks so smoke can be added.
    """
    rng = random.Random(seed)
    shapes: list[str] = []
    windows: list[str] = []
    stacks: list[tuple[float, float]] = []
    x = x0 - rng.uniform(0, 20)
    while x < x1:
        kind = rng.choices(("block", "stack", "tank", "gantry"), (5, 2, 1.3, 1))[0]
        if kind == "block":
            w = rng.uniform(26, 74)
            h = rng.uniform(max_h * 0.25, max_h * 0.72)
            top = base - h
            d = f"M{x:.0f} {base}V{top:.0f}H{x + w:.0f}V{base}Z"
            if rng.random() < 0.5:  # stepped roof
                sw = w * rng.uniform(0.3, 0.6)
                sx = x + rng.uniform(0, w - sw)
                sh = rng.uniform(6, 18)
                d += f"M{sx:.0f} {top:.0f}V{top - sh:.0f}H{sx + sw:.0f}V{top:.0f}Z"
            shapes.append(f'<path d="{d}"/>')
            if rng.random() < 0.4:  # antenna
                ax = x + rng.uniform(4, w - 4)
                shapes.append(f'<path d="M{ax:.0f} {top:.0f}V{top - rng.uniform(10, 26):.0f}" stroke="{fill}" stroke-width="1.5"/>')
            if lights:
                for _ in range(rng.randint(0, 4)):
                    wx = x + 4 + rng.uniform(0, max(w - 10, 1))
                    wy = top + 6 + rng.uniform(0, max(h - 20, 1))
                    cls = ' class="win"' if rng.random() < 0.25 else ' opacity=".7"'
                    windows.append(
                        f'<rect{cls} x="{wx:.0f}" y="{wy:.0f}" width="3" height="4" fill="{BRASS}" '
                        f'style="animation-delay:-{rng.uniform(0, 7):.1f}s"/>'
                    )
            x += w + rng.choice((0, 0, 2, 6))
        elif kind == "stack":
            w = rng.uniform(7, 12)
            h = rng.uniform(max_h * 0.7, max_h)
            top = base - h
            shapes.append(
                f'<path d="M{x:.0f} {base}V{top:.0f}H{x + w:.0f}V{base}Z'
                f'M{x - 2:.0f} {top:.0f}V{top - 5:.0f}H{x + w + 2:.0f}V{top:.0f}Z"/>'
            )
            for band in range(int(top) + 14, int(base) - 6, 16):
                shapes.append(f'<rect x="{x - 1:.0f}" y="{band}" width="{w + 2:.0f}" height="2"/>')
            stacks.append((x + w / 2, top - 5))
            x += w + rng.uniform(6, 18)
        elif kind == "tank":
            w = rng.uniform(34, 56)
            h = rng.uniform(24, 46)
            top = base - h
            c = w * 0.22
            shapes.append(
                f'<path d="M{x:.0f} {base}V{top:.0f}L{x + c:.0f} {top - c * .6:.0f}'
                f'H{x + w - c:.0f}L{x + w:.0f} {top:.0f}V{base}Z"/>'
            )
            x += w + rng.uniform(2, 8)
        else:  # gantry / crane lattice
            w = rng.uniform(30, 48)
            h = rng.uniform(max_h * 0.45, max_h * 0.8)
            top = base - h
            lines = [f"M{x:.0f} {base}V{top:.0f}M{x + w:.0f} {base}V{top:.0f}M{x:.0f} {top:.0f}H{x + w + 26:.0f}"]
            step = 14
            y = base
            while y - step > top:
                lines.append(f"M{x:.0f} {y:.0f}L{x + w:.0f} {y - step:.0f}M{x:.0f} {y - step:.0f}H{x + w:.0f}")
                y -= step
            lines.append(f"M{x + w + 22:.0f} {top:.0f}V{top + rng.uniform(18, 40):.0f}")
            shapes.append(f'<path d="{"".join(lines)}" fill="none" stroke="{fill}" stroke-width="1.5"/>')
            x += w + rng.uniform(4, 14)
    body = f'<g fill="{fill}" class="cr">{"".join(shapes)}</g>' + "".join(windows)
    return body, stacks


def smoke(stacks: list[tuple[float, float]], color: str = "#3b332d", seed: int = 1) -> str:
    """Hard-edged stepped plumes drifting up from each stack."""
    rng = random.Random(seed)
    out = []
    for sx, sy in stacks:
        for i in range(3):
            s = rng.uniform(6, 11)
            pts = " ".join(
                f"{sx + dx * s:.1f},{sy + dy * s:.1f}"
                for dx, dy in ((-1, 0), (-0.6, -0.9), (0.4, -1.1), (1.1, -0.4), (0.8, 0.5), (-0.3, 0.7))
            )
            out.append(
                f'<polygon class="smoke" points="{pts}" fill="{color}" '
                f'style="animation-delay:-{i * 3.3 + rng.uniform(0, 1.5):.1f}s"/>'
            )
    return "".join(out)


def smog(x: float, y: float, width: float, height: float, bands: int = 6) -> str:
    """Stepped haze: stacked flat bands, no gradients."""
    step = height / bands
    return "".join(
        f'<rect class="cr" x="{x}" y="{y + i * step:.1f}" width="{width}" height="{height - i * step:.1f}" '
        f'fill="#3a302a" opacity=".07"/>'
        for i in range(bands)
    )


def desaturate(hex_color: str, amount: float = 0.55, darken: float = 0.82) -> str:
    """Push a language colour toward the grim palette."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    except (ValueError, AttributeError):
        return FADED
    grey = 0.3 * r + 0.59 * g + 0.11 * b
    mix = [((1 - amount) * c + amount * grey) * darken for c in (r, g, b)]
    return "#" + "".join(f"{max(0, min(255, int(c))):02x}" for c in mix)
