---
title: "Hello, world"
description: "First post — what this blog is, and how it is built."
date: 2026-11-07
tags: meta
---

## Why this blog

A place to write down what I learn and break: security research,
development notes, and the occasional war story. Writing things down is
how I make sure I actually understand them.

## How it is built

No framework, no database. Articles are Markdown files; a small Python
script builds the whole site into plain HTML:

```bash
python3 scripts/build.py
```

The source lives on [GitHub](https://github.com/farisxdo/farisxdo.github.io)
and is served by GitHub Pages. Light and dark mode included — your
browser preference decides, and the toggle in the header overrides it.

## What to expect

- Short, practical posts
- Code you can copy
- Occasional deep dives

> If something here is wrong, tell me — that is the fastest way for both
> of us to learn something.
