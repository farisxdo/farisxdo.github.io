# farisxdo.github.io

Personal technical blog — just articles, nothing else. Same minimal
black & white theme (light/dark) as the xdo website, which this build
system was derived from.

Built with plain HTML/CSS/JavaScript and a small Python build script.
No npm, no external fonts, no paid services.

## Quick start

Requirements: Python 3.8 or newer. Nothing else.

```bash
python3 scripts/build.py
python3 -m http.server 8000 --directory site
```

Then open http://localhost:8000/

Always preview through the local server (not by double-clicking the HTML
files) so that relative paths resolve correctly.

## Project structure

```text
farisxdo.github.io/
├── content.json              # blog settings and copy
├── scripts/build.py          # builds the static site into site/
├── templates/                # HTML templates used by the build script
├── articles/                 # articles (Markdown + front matter)
├── assets/                   # style.css, main.js, favicons (copied into site/)
├── .github/workflows/deploy.yml
└── site/                     # generated output — do not edit by hand
```

`site/` is regenerated on every build and is listed in `.gitignore` —
the GitHub Actions workflow builds the site on GitHub, so `site/` never
needs to be committed.

## Editing the blog copy

All blog text lives in **`content.json`**: site title and description,
the intro line on the home page, labels, and the footer. Edit, save,
rebuild, refresh.

## Writing articles

Articles are Markdown files directly in `articles/`, with a small
front-matter header:

```markdown
---
title: "Your article title"
description: "One-sentence summary shown on the article index."
date: 2026-11-07
tags: security, notes
draft: true
---

## First heading

Body text...
```

- `draft: true` keeps the article off the website. Set `draft: false`
  (or delete the line) and rebuild to publish.
- `tags:` is an optional comma-separated list. Tags appear on the
  article, on the index, and each tag gets its own archive page at
  `tag/<tag>/` (linked from the tag row on the home page). Keep tags
  lowercase, short and few (1–3 per article).
- Supported Markdown: `##`/`###` headings, paragraphs, bullet and
  numbered lists, **bold**, *italic*, `code`, fenced code blocks,
  links, `> quotes`, and `---` horizontal rules.
- The article URL is `articles/<filename>/` — the filename (without
  `.md`) becomes the slug, so use lowercase-with-dashes filenames.
- The build script prints how many articles were published and how many
  drafts were excluded, and fails if any internal link is broken.

## Deploying to GitHub Pages

The repository is named **`farisxdo.github.io`**, so GitHub serves it at
`https://farisxdo.github.io/` automatically.

1. Push the files to the `main` branch:

   ```bash
   git add .
   git commit -m "farisxdo blog"
   git push -u origin main
   ```

2. In the repository: Settings → Pages → Build and deployment →
   Source: **GitHub Actions**. The included workflow
   (`.github/workflows/deploy.yml`) builds the site and deploys it on
   every push to `main`.

Because the workflow builds the site on GitHub, `site/` is never
committed — keep it in `.gitignore`.

### Custom domain

If you ever point a custom domain at this blog, update
`content.json` → `site.domain` — it drives canonical URLs, the sitemap,
and `robots.txt`.

## The favicon

`assets/favicon.svg` is a theme-aware SVG (dark square with a light `f`
in light mode, inverted in dark mode), with `favicon-32.png` and
`favicon-180.png` (apple-touch-icon) as fallbacks. To replace them,
overwrite the files in `assets/` and rebuild.

## Analytics

Analytics is intentionally left unconfigured — no tracking provider
was added silently. When you choose one, paste its snippet into the
three template files (`templates/home.html`, `templates/article.html`,
`templates/tag.html`) just before `</body>`, and rebuild.

## Troubleshooting

**Changes not visible.** Hard-refresh (Cmd+Shift+R / Ctrl+F5) — the
browser may cache `style.css` or `main.js`.

**Build fails with a permission error.** Stop the preview server
(Ctrl+C) and run the build again. The build never deletes the whole
`site/` folder; it only removes files it generated itself (tracked in
`site/.build-manifest.json`).

## License

Split license — see [LICENSE](LICENSE) for the full text:

- Source code (`scripts/`, `templates/`, `assets/style.css`,
  `assets/main.js`, `assets/favicon.svg`): MIT
- Articles (`articles/`) and site copy (`content.json`): CC BY 4.0,
  attribution to farisxdo
