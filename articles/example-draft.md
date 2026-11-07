---
title: "Example draft article — delete or edit me"
description: "A draft showing the article format. It will not appear on the website until you remove the draft flag."
date: 2026-11-07
tags: example, draft
draft: true
---

## This is a draft

Files in `articles/` are drafts while `draft: true` stays in the front
matter — the block between the two `---` lines at the top of the file.

## How to publish

1. Edit the front matter: set a real `title`, `description` and `date`.
2. Change `draft: true` to `draft: false` (or delete the line).
3. Rebuild: `python3 scripts/build.py`.

The article appears on the home page, in its tag archives, and in
`sitemap.xml`.

## Markdown you can use

Headings with `##` and `###`, bullet and numbered lists, **bold**,
*italic*, `inline code`, links [to GitHub](https://github.com/farisxdo)
and fenced code blocks:

```bash
python3 scripts/build.py
```

> Blockquotes are supported too.
