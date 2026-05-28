# jangrundl.de — My personal site & journal

This is my personal portfolio and journal, built with Jekyll and hosted on GitHub Pages. I use it to keep track of what I'm reading, writing, and building.

---

## How I add blog posts

I publish new entries by adding Markdown files to the `_posts/` directory.

1. I create a file in **`_posts/`**.
2. I name it **`YYYY-MM-DD-a-short-title.md`**.
3. I add the front matter block at the top:

   ```yaml
   ---
   layout: post
   title: "My Post Title"
   subtitle: "An optional one-line subtitle"
   date: 2026-06-01
   tags: [software, reading]
   description: "A short teaser for the home page and journal list."
   ---
   ```

4. I write the post in Markdown below that, then commit and push. GitHub Pages handles the build automatically.

### Markdown I use
I use standard Markdown: headings, bold, italics, lists, and code blocks. For images, I drop them in `assets/img/` and link them like this:

```markdown
![Alt text]({{ "/assets/img/your-image.jpg" | relative_url }})
```

---

## Folder map

```
index.html                 My home page (hero, about, journal preview)
journal.html               The full blog index (/journal/)
_posts/                    Where I keep my entries
_layouts/
  default.html             The site shell (nav, footer)
  post.html                The template for single posts
assets/
  css/style.css            All my styling
  img/                     Site images and post assets
_config.yml                Jekyll configuration
CNAME                      My custom domain setup
Gemfile                    For local development
```

---

## How I host this on GitHub Pages

1. I pushed this repository to GitHub.
2. In **Settings → Pages**, I set the source to **Deploy from a branch** (main).
3. The site is live at [jangrundl.de](https://www.jangrundl.de).

### My `baseurl` setting
In `_config.yml`, I keep `baseurl` empty because I use a custom domain:
```yaml
baseurl: ""
```

---

## My automated draft pipeline

I've built a pipeline that suggests draft posts for me on a schedule. It uses the Gemini API to find interesting tech news and draft a starting point. **Nothing is ever published automatically** — it just opens a Pull Request that I have to review, edit, and merge.

### How it works
- **Phase 1 (Automatic):** A GitHub Action (`.github/workflows/generate.yml`) runs twice a day. It triggers `scripts/generate_content.py` which pulls from TechCrunch or arXiv, asks Gemini 2.5 Flash for a draft, and opens a PR.
- **Phase 2 (Review):** I look over the PR, rewrite the parts that don't sound like me, flip the status from `draft` to `published`, and merge it to the site.
- I use `data/posted.json` to make sure the same source article isn't used twice.

### How to set it up
1. Add a `GEMINI_API_KEY` to repository secrets.
2. Ensure the GitHub Actions runner has **Read and write permissions** to create Pull Requests.
3. The schedule is set in the workflow file, but I can also trigger it manually from the **Actions** tab.

### Tuning the voice
I keep the persona and "banned words" list in `scripts/prompts.py`. If I want to change where the drafts come from, I edit the `SOURCES` in `scripts/generate_content.py`.

---

## My Instagram carousel tool

I wrote `scripts/instagram_post.py` to help me turn blog posts into Instagram carousels. It's a local tool I run by hand.

```bash
# How I run it:
python scripts/instagram_post.py            # Use the newest post
python scripts/instagram_post.py --post _posts/filename.md
```

It takes a post, asks Gemini to condense it into a few punchy slides, and then renders branded PNGs that match my site's aesthetic. I then upload these manually.

### Brand assets
- **Logo:** It looks for `assets/logo.png`. If it's missing, it draws a "JVG" monogram seal.
- **Fonts:** It uses EB Garamond from `assets/fonts/` so the slides match the website.

---

## Previewing locally

When I want to see changes before pushing, I run:

```bash
bundle exec jekyll serve
```

---

## Notes on the design

- I use the Open Library API to pull book covers for the home page.
- Fonts are Cormorant Garamond and EB Garamond.
- The RSS feed is at `/feed.xml`.
- I have "Older" and "Newer" navigation at the bottom of every post.
