#!/usr/bin/env python3
"""Build the Open Graph card -- the preview Discord, Slack, LinkedIn and
WhatsApp show when the site is pasted into a chat.

The card is deliberately the *same* design as the page: cream paper, the same
ink and accent green read straight from the CSS custom properties in
index.html, DM Sans for the name, Inter for everything else, and the identical
topographic contour field the page draws on its canvas -- the wave table and
the marching-squares pass below are a direct port of the JS in index.html, so
the card and the page cannot drift apart.

    pip install pillow && python3 scripts/build_og.py

Fonts are the Google Fonts variable TTFs. They are not in the repo (the page
loads them from the Google CDN at runtime); this script downloads them into
scripts/fonts/ on first run, which .gitignore excludes.
"""

from __future__ import annotations

import math
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
PORTRAIT = ROOT / "assets" / "img" / "hero.jpg"
OUT = ROOT / "assets" / "img" / "og-card.png"

FONT_DIR = Path(__file__).resolve().parent / "fonts"
FONTS = {
    "DMSans.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/dmsans/DMSans%5Bopsz,wght%5D.ttf",
    "Inter.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf",
}

# Open Graph's standard card. Discord, Slack and LinkedIn all render 1.91:1.
W, H = 1200, 630
SS = 3  # supersampling factor; PIL draws aliased lines, so render big and shrink

# ---------------------------------------------------------------- the words --
KICKER = "ROSTOCK, GERMANY"
NAME = "Jan Victornino Grundl"
ROLE = "Research Assistant  ·  Software Developer"
DETAIL = "LLM agents  ·  IoT sensor systems  ·  software engineering"
SITE = "jangrundl.de"
HANDLE = "github.com/jg512"


def css_vars() -> dict[str, str]:
    """Read the light-mode palette out of index.html so the card cannot drift.

    Only the bare `:root` block is parsed -- the [data-theme="dark"] block that
    follows it redefines the same names and must not win here.
    """
    src = INDEX.read_text(encoding="utf-8")
    block = re.search(r":root\s*\{(.*?)\}", src, re.S)
    if not block:
        raise SystemExit("could not find the :root block in index.html")
    out = dict(re.findall(r"--([\w-]+)\s*:\s*([^;]+);", block.group(1)))
    return {k: v.strip() for k, v in out.items()}


def hex_rgb(value: str) -> tuple[int, int, int]:
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def font(name: str, size: int, weight: int, opsz: float | None = None) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / name
    if not path.exists():
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"  downloading {name} ...")
        urllib.request.urlretrieve(FONTS[name], path)
    f = ImageFont.truetype(str(path), size * SS)
    axes = f.get_variation_axes()
    coords = []
    for axis in axes:
        label = axis["name"].decode() if isinstance(axis["name"], bytes) else axis["name"]
        target = weight if label.lower().startswith("weight") else (opsz if opsz else size)
        coords.append(max(axis["minimum"], min(axis["maximum"], target)))
    f.set_variation_by_axes(coords)
    return f


def topo_layer(rgb: tuple[int, int, int], a_line: float, a_index: float) -> Image.Image:
    """The page's contour field, ported from the canvas code in index.html.

    Same six drifting sine waves, same vertical tilt, same eleven levels with
    every third one drawn as a heavier index line. `t` is fixed at 0, so this
    is the first frame of the page's animation.
    """
    CELL, LREF, LEVELS, INDEX_EVERY = 24, 900, 11, 3
    waves = [
        (0.55, 0.32, 1.00, 0.0),
        (0.90, -0.20, 0.70, 1.7),
        (1.45, 0.55, 0.52, 3.1),
        (0.38, 0.85, 0.60, 4.4),
        (2.10, -0.42, 0.34, 5.6),
        (1.15, 1.20, 0.30, 2.3),
    ]
    cols = math.ceil(W / CELL) + 1
    rows = math.ceil(H / CELL) + 1
    sx = 2 * math.pi / LREF

    vals = [0.0] * (cols * rows)
    lo, hi, i = float("inf"), float("-inf"), 0
    for gy in range(rows):
        y = gy * CELL
        for gx in range(cols):
            x = gx * CELL
            v = sum(amp * math.sin(kx * sx * x + ky * sx * y + ph)
                    for kx, ky, amp, ph in waves)
            v += (y / H) * 0.35
            vals[i] = v
            i += 1
            lo, hi = min(lo, v), max(hi, v)

    layer = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    if hi - lo < 1e-6:
        return layer

    def ip(a: float, b: float, level: float) -> float:
        d = b - a
        return 0.5 if d == 0 else (level - a) / d

    for L in range(1, LEVELS):
        level = lo + (hi - lo) * (L / LEVELS)
        is_index = L % INDEX_EVERY == 0
        alpha = a_index if is_index else a_line
        colour = (*rgb, max(1, round(alpha * 255)))
        width = round((1.2 if is_index else 1.0) * SS)

        for gy in range(rows - 1):
            for gx in range(cols - 1):
                i0 = gy * cols + gx
                a, b = vals[i0], vals[i0 + 1]
                c, d = vals[i0 + cols + 1], vals[i0 + cols]
                code = ((8 if a > level else 0) | (4 if b > level else 0)
                        | (2 if c > level else 0) | (1 if d > level else 0))
                if code in (0, 15):
                    continue
                x, y = gx * CELL, gy * CELL
                top = (x + CELL * ip(a, b, level), y)
                right = (x + CELL, y + CELL * ip(b, c, level))
                bottom = (x + CELL * ip(d, c, level), y + CELL)
                left = (x, y + CELL * ip(a, d, level))
                pairs = {
                    1: [(left, bottom)], 14: [(left, bottom)],
                    2: [(bottom, right)], 13: [(bottom, right)],
                    3: [(left, right)], 12: [(left, right)],
                    4: [(top, right)], 11: [(top, right)],
                    5: [(left, top), (bottom, right)],
                    6: [(top, bottom)], 9: [(top, bottom)],
                    7: [(left, top)], 8: [(left, top)],
                    10: [(left, bottom), (top, right)],
                }[code]
                for p1, p2 in pairs:
                    draw.line([(p1[0] * SS, p1[1] * SS), (p2[0] * SS, p2[1] * SS)],
                              fill=colour, width=width)
    return layer


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1],
                                        radius=radius, fill=255)
    return m


def tracked(draw: ImageDraw.ImageDraw, xy, text, f, fill, tracking):
    """Draw text with letter-spacing; PIL has no tracking of its own."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + tracking * SS
    return x


def build() -> None:
    v = css_vars()
    bg = hex_rgb(v["bg"])
    ink = hex_rgb(v["ink"])
    ink_soft = hex_rgb(v["ink-soft"])
    muted = hex_rgb(v["muted"])
    accent = hex_rgb(v["accent"])
    surface = hex_rgb(v["surface"])
    border = hex_rgb(v["border"])
    topo_rgb = tuple(int(n) for n in v["topo"].split(","))
    a_line = float(v["topo-line"])
    a_index = float(v["topo-index"])

    img = Image.new("RGB", (W * SS, H * SS), bg)
    img.paste(Image.alpha_composite(
        Image.new("RGBA", (W * SS, H * SS), (*bg, 255)),
        topo_layer(topo_rgb, a_line, a_index)).convert("RGB"), (0, 0))

    # ---- the card panel: the page's .card surface, scaled up ----------------
    pad, radius = 52, 30
    box = (pad, pad, W - pad, H - pad)
    bw, bh = box[2] - box[0], box[3] - box[1]

    shadow = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [box[0] * SS, (box[1] + 10) * SS, box[2] * SS, (box[3] + 12) * SS],
        radius=radius * SS, fill=(25, 25, 23, 46))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14 * SS))
    img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")

    panel = Image.new("RGB", (bw * SS, bh * SS), surface)
    img.paste(panel, (box[0] * SS, box[1] * SS), rounded_mask((bw * SS, bh * SS), radius * SS))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([box[0] * SS, box[1] * SS, box[2] * SS - 1, box[3] * SS - 1],
                        radius=radius * SS, outline=border, width=max(1, SS))

    # ---- portrait, right-hand side -----------------------------------------
    inner = 44
    ph = bh - inner * 2
    pw = round(ph * 0.75)
    px2, py1 = box[2] - inner, box[1] + inner
    px1 = px2 - pw

    photo = Image.open(PORTRAIT).convert("RGB")
    # Drop the top of the frame first. The page can afford all that sky because
    # it renders the portrait 430 px tall; in a chat embed the card is a few
    # hundred pixels wide, and the face has to survive that.
    ZOOM = 0.86
    photo = photo.crop((0, round(photo.height * (1 - ZOOM)), photo.width, photo.height))

    target = pw / ph
    src = photo.width / photo.height
    if src > target:                      # too wide -> trim the sides
        new_w = round(photo.height * target)
        left = (photo.width - new_w) // 2
        photo = photo.crop((left, 0, left + new_w, photo.height))
    else:                                 # too tall -> trim from the bottom
        new_h = round(photo.width / target)
        photo = photo.crop((0, 0, photo.width, new_h))
    photo = photo.resize((pw * SS, ph * SS), Image.LANCZOS)
    img.paste(photo, (px1 * SS, py1 * SS), rounded_mask((pw * SS, ph * SS), 18 * SS))

    # ---- the text block, left ----------------------------------------------
    x = box[0] + inner
    right_edge = px1 - 44
    avail = right_edge - x

    f_kicker = font("Inter.ttf", 15, 600)
    f_role = font("Inter.ttf", 22, 500)
    f_detail = font("Inter.ttf", 18, 400)
    f_site = font("Inter.ttf", 19, 600)
    f_handle = font("Inter.ttf", 19, 400)

    # The name is the one line that can overflow, so fit it to the column.
    size = 62
    while size > 34:
        f_name = font("DMSans.ttf", size, 500, opsz=40)
        if d.textlength(NAME, font=f_name) <= avail * SS:
            break
        size -= 2

    # Footer sits on the panel's baseline; everything above it is one group,
    # optically centred in the space that leaves. Laying it out by stacked
    # offsets alone left a dead band across the middle of the card.
    fy = box[3] - inner - 22
    steps = (34, size + 26, 3 + 30, 36)          # kicker, name, rule, role
    group_h = sum(steps) + 24                    # + the detail line's own height
    top, bottom = box[1] + inner, fy - 26
    y = top + max(0, (bottom - top - group_h) // 2)

    tracked(d, (x * SS, y * SS), KICKER, f_kicker, muted, 2.2)
    y += steps[0]
    d.text((x * SS, y * SS), NAME, font=f_name, fill=ink)
    y += steps[1]
    d.rectangle([x * SS, y * SS, (x + 62) * SS, (y + 3) * SS], fill=accent)
    y += steps[2]
    d.text((x * SS, y * SS), ROLE, font=f_role, fill=ink_soft)
    y += steps[3]
    d.text((x * SS, y * SS), DETAIL, font=f_detail, fill=muted)

    d.text((x * SS, fy * SS), SITE, font=f_site, fill=accent)
    sep_x = x + d.textlength(SITE, font=f_site) / SS + 14
    d.text((sep_x * SS, fy * SS), "·", font=f_handle, fill=muted)
    d.text(((sep_x + 16) * SS, fy * SS), HANDLE, font=f_handle, fill=muted)

    img = img.resize((W, H), Image.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size / 1024:.0f} KB, {W}x{H})")


if __name__ == "__main__":
    build()
