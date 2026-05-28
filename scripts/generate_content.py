#!/usr/bin/env python3
"""
Phase 1 - The Generator.

Runs on a schedule from GitHub Actions:
  1. (evening only) flip a coin; 50% of the time exit cleanly and post nothing.
  2. Pick a source (TechCrunch or arXiv cs.AI) and a mode (deep-dive / roundup).
  3. Pull the latest items, skip anything already used (data/posted.json).
  4. Ask Gemini 2.5 Flash for a post as structured JSON.
  5. Enforce the 2-8 minute reading-time band, retrying if needed.
  6. Write a Jekyll post into _posts/ with full front matter.
  7. Record the source id so we never repeat it.

The workflow then opens a Pull Request with the new files. Nothing is published
until you review and merge that PR. That is the entire human-in-the-loop.

Uses the current Google Gen AI SDK (`google-genai`); the older
`google-generativeai` package was deprecated in 2025.
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import feedparser
from google import genai
from google.genai import types
from pydantic import BaseModel
from slugify import slugify

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts"
STATE_FILE = ROOT / "data" / "posted.json"

MODEL = "gemini-2.5-flash"
TEMPERATURE = 0.9

WORDS_PER_MINUTE = 230
MIN_MINUTES, MAX_MINUTES = 2, 8
MAX_RETRIES = 3              # regeneration attempts to land inside the band
KEEP_HISTORY = 400          # how many used-ids to remember

SOURCES = {
    "techcrunch": {
        "label": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "modes": ["deep_dive", "roundup"],
    },
    "hacker_news": {
        "label": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "modes": ["deep_dive", "roundup"],
    },
    "the_verge": {
        "label": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "modes": ["deep_dive", "roundup"],
    },
    "ars_technica": {
        "label": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "modes": ["deep_dive", "roundup"],
    },
    "arxiv": {
        "label": "arXiv cs.AI",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "modes": ["deep_dive"],
    },
}
TOP_N = 5  # consider the newest 5 items for variety


# --------------------------------------------------------------------------- #
# Structured-output schema  (Gemini returns exactly this shape)
# --------------------------------------------------------------------------- #
class Post(BaseModel):
    title: str          # 6-10 words, no clickbait
    markdown_body: str  # the essay, Markdown, no H1/title inside
    tags: list[str]     # 2-4 lowercase tags


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def log(msg: str) -> None:
    print(f"[generate] {msg}", flush=True)


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"used_ids": []}


def save_state(state: dict) -> None:
    state["used_ids"] = state["used_ids"][-KEEP_HISTORY:]
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w[\w'-]*\b", text))


def reading_minutes(text: str) -> int:
    return max(1, round(word_count(text) / WORDS_PER_MINUTE))


def clean_summary(html: str, limit: int = 1500) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def first_paragraph(markdown: str, limit: int = 180) -> str:
    """First real prose line, skipping headings, blockquotes and bullets."""
    for line in markdown.strip().splitlines():
        s = line.strip()
        if not s or s.startswith(("#", ">", "-", "*", "`", "|")):
            continue
        s = re.sub(r"[*_`]", "", s)          # strip inline markdown
        return s[:limit].replace('"', "'").strip()
    return "A new entry."


# --------------------------------------------------------------------------- #
# Source selection
# --------------------------------------------------------------------------- #
def pick_item(state: dict):
    """Return (source_key, mode, item) for a fresh article, or raise."""
    order = list(SOURCES.keys())
    random.shuffle(order)
    for key in order:
        src = SOURCES[key]
        feed = feedparser.parse(src["url"])
        if not feed.entries:
            log(f"{src['label']}: no entries, trying next source")
            continue
        candidates = feed.entries[:TOP_N]
        fresh = [e for e in candidates
                 if (e.get("id") or e.get("link")) not in state["used_ids"]]
        if not fresh:
            log(f"{src['label']}: top {TOP_N} all seen, trying next source")
            continue
        item = random.choice(fresh)
        mode = random.choice(src["modes"])
        # For a roundup we still need the sibling headlines for context.
        item._siblings = candidates  # type: ignore[attr-defined]
        return key, mode, item
    raise RuntimeError("No fresh items in any source right now.")


def build_context(source_key: str, mode: str, item) -> str:
    src = SOURCES[source_key]
    if mode == "roundup":
        lines = []
        for e in item._siblings:  # type: ignore[attr-defined]
            lines.append(f"- {e.get('title','(untitled)')}: "
                         f"{clean_summary(e.get('summary',''), 300)}")
        return f"Source: {src['label']}\n" + "\n".join(lines)
    # deep dive
    return (
        f"Source: {src['label']}\n"
        f"Title: {item.get('title','(untitled)')}\n"
        f"Link: {item.get('link','')}\n"
        f"Summary/Abstract: {clean_summary(item.get('summary',''))}"
    )


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #
def make_prompt(mode: str, context: str) -> str:
    import prompts
    # word band derived from the reading-time band, with a little slack
    lo, hi = MIN_MINUTES * WORDS_PER_MINUTE, MAX_MINUTES * WORDS_PER_MINUTE
    # aim for the comfortable middle so retries are rare
    aim_lo, aim_hi = 4 * WORDS_PER_MINUTE, 6 * WORDS_PER_MINUTE
    target = prompts.TARGET_BLOCK.format(
        lo=aim_lo, hi=aim_hi, tlo=4, thi=6, floor=lo, ceil=hi
    )
    tmpl = prompts.DEEP_DIVE_TEMPLATE if mode == "deep_dive" else prompts.ROUNDUP_TEMPLATE
    return tmpl.format(context=context, target=target)


def generate(client: genai.Client, mode: str, context: str) -> Post:
    import prompts
    prompt = make_prompt(mode, context)
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        nudge = ""
        if last_err:
            nudge = f"\n\nNOTE: your previous attempt was {last_err}. Adjust the length."
        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt + nudge,
            config=types.GenerateContentConfig(
                system_instruction=prompts.SYSTEM_INSTRUCTION,
                temperature=TEMPERATURE,
                response_mime_type="application/json",
                response_schema=Post,
            ),
        )
        post: Post = resp.parsed  # type: ignore[assignment]
        mins = reading_minutes(post.markdown_body)
        wc = word_count(post.markdown_body)
        log(f"attempt {attempt}: {wc} words ~ {mins} min")
        if MIN_MINUTES <= mins <= MAX_MINUTES:
            return post
        last_err = f"too short ({mins} min)" if mins < MIN_MINUTES else f"too long ({mins} min)"
    raise RuntimeError(f"Could not land in the {MIN_MINUTES}-{MAX_MINUTES} min band "
                       f"after {MAX_RETRIES} tries (last: {last_err}).")


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def write_post(post: Post, source_key: str, item, mode: str) -> Path:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    slug = slugify(post.title)[:60] or "untitled"
    path = POSTS_DIR / f"{date_str}-{slug}.md"

    canonical = f"https://www.jangrundl.de/journal/{slug}/"
    tags = ", ".join(t.strip().lower() for t in post.tags[:4])
    src_url = item.get("link", "")
    src_label = SOURCES[source_key]["label"]
    safe_title = post.title.replace('"', "'")
    subtitle = "A draft from the pipeline -- review before publishing."

    front = f"""---
layout: post
title: "{safe_title}"
subtitle: "{subtitle}"
date: {now.strftime('%Y-%m-%d %H:%M:%S %z')}
tags: [{tags}]
description: "{first_paragraph(post.markdown_body)}"
canonical_url: {canonical}
source_label: "{src_label}"
source_url: {src_url}
mode: {mode}
status: draft
---
"""

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(front + "\n" + post.markdown_body.strip() + "\n",
                    encoding="utf-8")
    return path


def github_output(**kv) -> None:
    """Expose values to later workflow steps."""
    out = os.environ.get("GITHUB_OUTPUT")
    if not out:
        return
    with open(out, "a", encoding="utf-8") as fh:
        for k, v in kv.items():
            fh.write(f"{k}={v}\n")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    # Coin flip for the evening run only (workflow passes RUN_KIND=evening).
    if os.environ.get("RUN_KIND") == "evening" and random.random() < 0.5:
        log("Evening coin flip: tails. Skipping cleanly.")
        github_output(created="false")
        sys.exit(0)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log("GEMINI_API_KEY is not set.")
        sys.exit(1)
    client = genai.Client(api_key=api_key)

    state = load_state()
    source_key, mode, item = pick_item(state)
    log(f"Source={SOURCES[source_key]['label']} mode={mode} "
        f"item={item.get('title','?')[:70]!r}")

    context = build_context(source_key, mode, item)
    post = generate(client, mode, context)
    path = write_post(post, source_key, item, mode)
    log(f"Wrote {path.relative_to(ROOT)}")

    state["used_ids"].append(item.get("id") or item.get("link"))
    save_state(state)

    github_output(
        created="true",
        post_path=str(path.relative_to(ROOT)),
        post_title=post.title,
        source=SOURCES[source_key]["label"],
        mode=mode,
    )


if __name__ == "__main__":
    main()
