#!/usr/bin/env python3
"""
Instagram carousel generator  (run by hand, you upload manually).

Reads your most recent post, asks Gemini to condense it into a hook + a few
punchy slides + a caption, then renders a set of branded PNG slides that match
the site's look. Output lands in `instagram/<slug>/` for you to upload yourself.

    python scripts/instagram_post.py            # newest post
    python scripts/instagram_post.py --post _posts/2026-05-12-....md
    python scripts/instagram_post.py --dry-run  # use sample text, no API call

This is intentionally NOT wired into the GitHub Actions pipeline. It's a local
tool. Uploading stays manual.

Brand assets:
  - Fonts: assets/fonts/EBGaramond*.ttf  (bundled).
  - Logo: assets/logo.png if present; otherwise a placeholder monogram is drawn.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts"
FONT_DIR = ROOT / "assets" / "fonts"
LOGO_PATH = ROOT / "assets" / "logo.png"          # optional; placeholder if absent
OUT_ROOT = ROOT / "instagram"

# ---- canvas (Instagram portrait 4:5, the most screen-space in feed) --------
W, H = 1080, 1350
MARGIN = 96

# ---- brand palette (matches the site CSS) ----------------------------------
PAPER       = (241, 232, 214)
PAPER_2     = (236, 225, 203)
INK         = (36, 29, 21)
INK_SOFT    = (79, 67, 52)
INK_FAINT   = (122, 107, 84)
GREEN_DEEP  = (42, 58, 44)
SIENNA      = (156, 86, 47)
SIENNA_DEEP = (125, 67, 36)
BRASS       = (169, 140, 90)
SEAL_TEXT   = (246, 234, 212)

MODEL = "gemini-2.5-flash"


# --------------------------------------------------------------------------- #
# Fonts
# --------------------------------------------------------------------------- #
def _font(size: int, weight: str = "Regular", italic: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / ("EBGaramond-Italic.ttf" if italic else "EBGaramond.ttf")
    f = ImageFont.truetype(str(path), size)
    if not italic:
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
    return f


# --------------------------------------------------------------------------- #
# Front matter / post loading
# --------------------------------------------------------------------------- #
def latest_post() -> Path:
    posts = sorted(POSTS_DIR.glob("*.md"))
    if not posts:
        raise SystemExit("No posts found in _posts/.")
    return posts[-1]


def parse_post(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise SystemExit(f"{path.name} has no front matter.")
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    body = m.group(2)
    body = re.sub(r"^>.*$", "", body, flags=re.M)        # drop the disclosure quote
    body = re.sub(r"[#>*`_]", "", body)                  # strip markdown marks
    body = re.sub(r"\n{2,}", "\n\n", body).strip()
    return {"front": fm, "body": body, "slug": path.stem[11:]}


# --------------------------------------------------------------------------- #
# Gemini: condense into slides + caption  (structured output)
# --------------------------------------------------------------------------- #
def condense(post: dict) -> dict:
    from google import genai
    from google.genai import types
    from pydantic import BaseModel

    class Slide(BaseModel):
        heading: str          # 2-5 words
        line: str             # one punchy sentence, <= ~18 words

    class Carousel(BaseModel):
        hook: str             # cover line, <= 9 words, makes someone stop scrolling
        slides: list[Slide]   # 3 to 4 slides
        caption: str          # engaging IG caption, a few short lines
        hashtags: list[str]   # 8-12, no '#'

    system = (
        "You turn a long essay into an Instagram carousel for a tech enthusiast "
        "and lifelong learner in their early twenties. Voice: personal, reflective, "
        "warm, and informative. No emojis anywhere. No banned filler (delve, "
        "landscape, game-changer, revolutionary). The hook should be an inviting "
        "personal observation. Each slide is one idea: a short heading and one "
        "thoughtful sentence. The caption is a few short lines that share a "
        "reflection and nudge to the link in bio. Hashtags relevant, lowercase, no spaces."
    )
    prompt = (
        f"TITLE: {post['front'].get('title','')}\n"
        f"SUBTITLE: {post['front'].get('subtitle','')}\n\n"
        f"ESSAY:\n{post['body'][:6000]}"
    )
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.85,
            response_mime_type="application/json",
            response_schema=Carousel,
        ),
    )
    return json.loads(resp.text)


def sample_content(post: dict) -> dict:
    """Used by --dry-run so you can design slides without spending a call."""
    return {
        "hook": "The demo was great. The product wasn't.",
        "slides": [
            {"heading": "The Pitch", "line": "Another launch promised to change everything by Tuesday."},
            {"heading": "The Reality", "line": "What shipped was a faster autocomplete with a press release."},
            {"heading": "Why It Matters", "line": "We keep grading intentions instead of what actually ships."},
        ],
        "caption": ("A short, honest read on the latest launch hype.\n\n"
                    "Less spec sheet, more so-what.\n\nFull essay: link in bio."),
        "hashtags": ["tech", "ai", "technology", "writing", "essay",
                     "siliconvalley", "criticalthinking", "startups"],
    }


# --------------------------------------------------------------------------- #
# Drawing helpers
# --------------------------------------------------------------------------- #
def base_canvas() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # soft top glow
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([-W // 2, -H, W + W // 2, H // 2], fill=70)
    img.paste(Image.new("RGB", (W, H), (255, 250, 238)), (0, 0),
              glow.filter(ImageFilter.GaussianBlur(160)))
    # paper grain
    import random
    rnd = random.Random(7)
    noise = Image.new("L", (W // 2, H // 2))
    noise.putdata([rnd.randint(120, 160) for _ in range((W // 2) * (H // 2))])
    noise = noise.resize((W, H)).filter(ImageFilter.GaussianBlur(0.6))
    img = Image.blend(img, Image.merge("RGB", (noise, noise, noise)), 0.05)
    d = ImageDraw.Draw(img)
    # double border frame
    d.rectangle([MARGIN - 34, MARGIN - 34, W - MARGIN + 34, H - MARGIN + 34],
                outline=tuple_a(INK, 60), width=2)
    d.rectangle([MARGIN - 24, MARGIN - 24, W - MARGIN + 24, H - MARGIN + 24],
                outline=tuple_a(INK, 28), width=1)
    return img


def tuple_a(rgb, a):
    """Approximate an alpha over PAPER (since base is opaque)."""
    return tuple(round(c * a / 255 + p * (1 - a / 255)) for c, p in zip(rgb, PAPER))


def draw_logo(img: Image.Image, cx: int, top: int) -> int:
    """Real logo if assets/logo.png exists, else a placeholder monogram seal."""
    d = ImageDraw.Draw(img)
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        lw = 150
        logo = logo.resize((lw, round(logo.height * lw / logo.width)))
        img.paste(logo, (cx - logo.width // 2, top), logo)
        return top + logo.height + 20
    # placeholder: monogram + ring + tiny "placeholder" tag
    r = 64
    cy = top + r
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=SIENNA_DEEP, width=3)
    mono = _font(46, "SemiBold")
    text = "JVG"
    tw = d.textlength(text, font=mono)
    d.text((cx - tw / 2, cy - 30), text, font=mono, fill=INK)
    tag = _font(15, "Medium")
    t2 = "PLACEHOLDER LOGO"
    d.text((cx - d.textlength(t2, font=tag) / 2, cy + r + 14), t2,
           font=tag, fill=INK_FAINT)
    return cy + r + 48


def wrap(d, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_centered_block(d, lines, font, top, fill, line_gap=1.18, max_w=None):
    asc, desc = font.getmetrics()
    lh = round((asc + desc) * line_gap)
    y = top
    for ln in lines:
        tw = d.textlength(ln, font=font)
        d.text(((W - tw) / 2, y), ln, font=font, fill=fill)
        y += lh
    return y


def ornament(d, y):
    d.text((W / 2 - 12, y), "\u2766", font=_font(40, "Regular"), fill=SIENNA)


# --------------------------------------------------------------------------- #
# Slide renderers
# --------------------------------------------------------------------------- #
def render_cover(data, post, idx, total):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    y = draw_logo(img, W // 2, MARGIN + 6)
    # kicker
    kick = _font(26, "Medium")
    label = (post["front"].get("source_label") or "Field Notes").upper()
    d.text((W / 2 - d.textlength(label, font=kick) / 2, y + 6), label,
           font=kick, fill=SIENNA_DEEP)
    # hook (the star of the cover)
    hook_font = _font(96, "SemiBold")
    lines = wrap(d, data["hook"], hook_font, W - 2 * MARGIN)
    block_h = len(lines) * round(sum(hook_font.getmetrics()) * 1.1)
    start = max(y + 90, (H - block_h) // 2 - 40)
    end = draw_centered_block(d, lines, hook_font, start, INK, 1.1)
    ornament(d, end + 24)
    # swipe cue
    cue = _font(30, "Medium", italic=True)
    swipe = "swipe \u2192"
    d.text((W / 2 - d.textlength(swipe, font=cue) / 2, H - MARGIN - 26), swipe,
           font=cue, fill=INK_FAINT)
    return img


def render_point(data, slide, n, idx, total):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    # big numeral
    num_font = _font(150, "Regular")
    num = f"{n:02d}"
    d.text((MARGIN + 4, MARGIN + 10), num, font=num_font, fill=tuple_a(BRASS, 150))
    # heading
    head = _font(72, "SemiBold")
    hlines = wrap(d, slide["heading"], head, W - 2 * MARGIN)
    y = MARGIN + 250
    for ln in hlines:
        d.text((MARGIN, y), ln, font=head, fill=INK)
        y += round(sum(head.getmetrics()) * 1.05)
    # rule
    y += 14
    d.line([MARGIN, y, MARGIN + 120, y], fill=SIENNA, width=3)
    y += 40
    # body line
    body = _font(50, "Regular")
    for ln in wrap(d, slide["line"], body, W - 2 * MARGIN):
        d.text((MARGIN, y), ln, font=body, fill=INK_SOFT)
        y += round(sum(body.getmetrics()) * 1.25)
    return img


def render_cta(data, post, idx, total):
    img = base_canvas()
    d = ImageDraw.Draw(img)
    y = draw_logo(img, W // 2, MARGIN + 30)
    big = _font(82, "SemiBold")
    lines = wrap(d, "Read the full essay", big, W - 2 * MARGIN)
    start = (H - len(lines) * round(sum(big.getmetrics()) * 1.1)) // 2 - 30
    end = draw_centered_block(d, lines, big, start, INK, 1.1)
    ornament(d, end + 20)
    sub = _font(40, "Regular", italic=True)
    note = "link in bio"
    d.text((W / 2 - d.textlength(note, font=sub) / 2, end + 80), note,
           font=sub, fill=SIENNA_DEEP)
    # domain footer
    foot = _font(30, "Medium")
    dom = "jangrundl.de"
    d.text((W / 2 - d.textlength(dom, font=foot) / 2, H - MARGIN - 20), dom,
           font=foot, fill=INK_FAINT)
    return img


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", help="path to a specific .md post")
    ap.add_argument("--dry-run", action="store_true",
                    help="use placeholder copy, skip the Gemini call")
    args = ap.parse_args()

    path = Path(args.post) if args.post else latest_post()
    post = parse_post(path)
    print(f"[ig] post: {path.name}")

    data = sample_content(post) if args.dry_run else condense(post)
    slides = data["slides"][:4]
    total = 1 + len(slides) + 1  # cover + points + CTA

    out_dir = OUT_ROOT / post["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)

    imgs = [render_cover(data, post, 0, total)]
    for i, s in enumerate(slides):
        imgs.append(render_point(data, s, i + 1, i + 1, total))
    imgs.append(render_cta(data, post, total - 1, total))

    paths = []
    for i, im in enumerate(imgs, 1):
        p = out_dir / f"slide_{i:02d}.png"
        im.save(p, "PNG")
        paths.append(p)

    caption = data["caption"].strip() + "\n\n" + \
        " ".join("#" + h.strip().lstrip("#") for h in data["hashtags"])
    (out_dir / "caption.txt").write_text(caption, encoding="utf-8")

    print(f"[ig] wrote {len(paths)} slides + caption.txt to {out_dir.relative_to(ROOT)}/")
    for p in paths:
        print("       ", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
