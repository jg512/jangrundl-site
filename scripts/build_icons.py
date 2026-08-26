#!/usr/bin/env python3
"""Build the JG mark: the favicon, the touch icon, and the nav logo.

One mark, three outputs, all from the same geometry -- a rounded square in the
page's accent green with the initials in the page's paper cream, set in DM Sans,
the same face the page uses for its headings.

    pip install pillow fonttools cairosvg && python3 scripts/build_icons.py

cairosvg needs the system libcairo; on Debian/Ubuntu that is libcairo2.

The letters are emitted as **outlines, not text**. The old favicon.svg was a
<text> element with font-family="Inter": SVG favicons do not load webfonts, so
every visitor without Inter installed locally got Helvetica or Arial instead.
Outlines render identically everywhere and need no font at all.

Colours come from the :root block of index.html, the same as scripts/build_og.py.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import cairosvg

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
FONT = Path(__file__).resolve().parent / "fonts" / "DMSans.ttf"

SVG_OUT = ROOT / "assets" / "img" / "favicon.svg"
PNG_OUT = ROOT / "assets" / "icon.png"

INITIALS = "JG"
WEIGHT = 700
BOX = 64          # the SVG viewBox; the PNG is rendered at 1024
RADIUS = 0.22     # corner radius as a fraction of the box -- iOS squircle-ish
CAP_RATIO = 0.42  # cap height as a fraction of the box; sized for 16 px tabs
TRACKING = -0.03  # em; DM Sans sets JG a touch loose for a monogram


def css_vars() -> dict[str, str]:
    """Palette from the bare :root block -- never the dark-theme override."""
    block = re.search(r":root\s*\{(.*?)\}", INDEX.read_text(encoding="utf-8"), re.S)
    if not block:
        raise SystemExit("could not find the :root block in index.html")
    return {k: v.strip() for k, v in re.findall(r"--([\w-]+)\s*:\s*([^;]+);", block.group(1))}


def outlines() -> tuple[str, float, float]:
    """Return (svg path data, advance width, cap height) in font units.

    The glyphs are laid out on one baseline with TRACKING applied between them,
    then returned as a single path so the SVG stays one element.
    """
    font = instantiateVariableFont(TTFont(FONT), {"wght": WEIGHT, "opsz": 40}, inplace=False)
    upem = font["head"].unitsPerEm
    cap = font["OS/2"].sCapHeight
    glyphset = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]

    parts, x = [], 0.0
    for ch in INITIALS:
        name = cmap[ord(ch)]
        pen = SVGPathPen(glyphset)
        # Flip Y here: font space is Y-up, SVG is Y-down.
        glyphset[name].draw(TransformPen(pen, (1, 0, 0, -1, x, 0)))
        parts.append(pen.getCommands())
        x += hmtx[name][0] + TRACKING * upem
    width = x - TRACKING * upem          # no tracking after the last glyph
    return " ".join(p for p in parts if p), width, cap


def build_svg(accent: str, paper: str) -> str:
    d, width, cap = outlines()
    scale = (CAP_RATIO * BOX) / cap
    tx = (BOX - width * scale) / 2
    ty = (BOX + cap * scale) / 2          # baseline, so the caps sit centred
    r = round(BOX * RADIUS, 2)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BOX} {BOX}" '
        f'width="{BOX}" height="{BOX}" role="img" aria-label="{INITIALS}">\n'
        f'  <rect width="{BOX}" height="{BOX}" rx="{r}" ry="{r}" fill="{accent}"/>\n'
        f'  <path transform="translate({tx:.3f} {ty:.3f}) scale({scale:.6f})" '
        f'fill="{paper}" d="{d}"/>\n'
        f'</svg>\n'
    )


def build_png(svg: str, size: int = 1024) -> None:
    """Rasterise the SVG rather than re-laying the type out.

    Laying the glyphs out a second time in PIL worked, but it put the mark's
    geometry in two places and the two drifted by a pixel or two. The SVG is
    the single source now; this is only a rendering of it.
    """
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                           output_width=size, output_height=size)
    Image.open(io.BytesIO(png)).convert("RGBA").save(PNG_OUT, "PNG", optimize=True)


def main() -> None:
    if not FONT.exists():
        raise SystemExit(f"missing {FONT} -- run scripts/build_og.py first, it downloads the fonts")
    v = css_vars()
    accent, paper = v["accent"], v["bg"]

    svg = build_svg(accent, paper)
    SVG_OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {SVG_OUT.relative_to(ROOT)}  ({SVG_OUT.stat().st_size} B, {accent} on {paper})")

    build_png(svg)
    print(f"wrote {PNG_OUT.relative_to(ROOT)}  ({PNG_OUT.stat().st_size / 1024:.0f} KB, 1024x1024)")


if __name__ == "__main__":
    main()
