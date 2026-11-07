#!/usr/bin/env python3
"""Build the farisxdo blog.

Zero dependencies: standard-library Python only (3.8+).

What it does:
- Reads blog settings from content.json
- Reads articles from articles/*.md (front matter + Markdown)
- Renders the static site into site/
  (home page = article index, plus article pages and tag archives)
- Copies assets/ into site/assets/
- Writes sitemap.xml, robots.txt and 404.html
- Cleans stale files from previous builds using a manifest
  (no wholesale folder deletion, which can fail on Windows)

Usage:
    python3 scripts/build.py
"""

import json
import re
import sys
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site"
MANIFEST = OUT / ".build-manifest.json"

ICON_SUN = (
    '<svg class="icon-sun" viewBox="0 0 24 24" aria-hidden="true">'
    '<circle cx="12" cy="12" r="5"/>'
    '<path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42'
    'M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
)
ICON_MOON = (
    '<svg class="icon-moon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
)


# ---------------------------------------------------------------------------
# Markdown (small subset: headings, paragraphs, lists, code, quotes, inline)
# ---------------------------------------------------------------------------

INLINE_PATTERNS = [
    (re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)"), r'<a href="\2">\1</a>'),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)"), r"<em>\1</em>"),
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
]


def inline(text: str) -> str:
    """Escape HTML, then apply inline Markdown."""
    text = escape(text, quote=False)
    for pattern, repl in INLINE_PATTERNS:
        text = pattern.sub(repl, text)
    return text


def render_markdown(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    html_out = []
    i = 0
    in_code = False
    code_lines = []
    list_type = None  # "ul" | "ol" | None

    def close_list():
        nonlocal list_type
        if list_type:
            html_out.append(f"</{list_type}>")
            list_type = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                html_out.append(
                    "<pre><code>" + escape("\n".join(code_lines), quote=False) + "</code></pre>"
                )
                code_lines = []
                in_code = False
            else:
                close_list()
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not stripped:
            close_list()
            i += 1
            continue

        m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if m:
            close_list()
            level = len(m.group(1)) + 1  # h2-h4 (title is the page h1)
            html_out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        m = re.match(r"^>\s?(.*)$", stripped)
        if m:
            close_list()
            html_out.append(f"<blockquote><p>{inline(m.group(1))}</p></blockquote>")
            i += 1
            continue

        if re.match(r"^(---|\*\*\*)$", stripped):
            close_list()
            html_out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^[-*]\s+(.*)$", stripped)
        if m:
            if list_type != "ul":
                close_list()
                html_out.append("<ul>")
                list_type = "ul"
            html_out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue

        m = re.match(r"^\d+\.\s+(.*)$", stripped)
        if m:
            if list_type != "ol":
                close_list()
                html_out.append("<ol>")
                list_type = "ol"
            html_out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue

        # paragraph: consume consecutive plain lines
        close_list()
        para = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (
                not nxt
                or nxt.startswith(("#", ">", "```", "- ", "* ", "---"))
                or re.match(r"^\d+\.\s", nxt)
            ):
                break
            para.append(nxt)
            i += 1
        html_out.append("<p>" + inline(" ".join(para)) + "</p>")

    close_list()
    if in_code:
        html_out.append(
            "<pre><code>" + escape("\n".join(code_lines), quote=False) + "</code></pre>"
        )
    return "\n".join(html_out)


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------

def parse_article(path: Path):
    """Parse front matter + body. Returns dict or None if unparsable."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---"):
        return None
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return None
    meta = {}
    for line in parts[0][3:].strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"')
    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    return {
        "slug": path.stem,
        "title": meta.get("title", path.stem),
        "description": meta.get("description", ""),
        "date": meta.get("date", ""),
        "draft": meta.get("draft", "").lower() == "true",
        "tags": tags,
        "body": render_markdown(parts[1].strip()),
    }


def load_articles(articles_dir: Path):
    articles = []
    if not articles_dir.is_dir():
        return articles
    for path in sorted(articles_dir.glob("*.md")):
        parsed = parse_article(path)
        if parsed:
            articles.append(parsed)
    return articles


def date_sort_key(article):
    try:
        return tuple(int(x) for x in article["date"].split("-"))
    except ValueError:
        return (0, 0, 0)


def tag_slug(tag: str) -> str:
    """URL-safe slug for a tag. Keeps Unicode letters (e.g. Chinese)."""
    slug = re.sub(r"\s+", "-", tag.strip().lower())
    return re.sub(r"[^\w-]", "", slug) or "tag"


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------

def render(template: str, values: dict) -> str:
    html = template
    for key, value in values.items():
        html = html.replace("{{" + key + "}}", str(value))
    leftover = re.findall(r"\{\{[A-Z0-9_]+\}\}", html)
    if leftover:
        raise ValueError(f"Unresolved template tokens: {sorted(set(leftover))}")
    return html


def build():
    content = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
    site = content["site"]
    blog = content["blog"]
    brand = site["brand"]

    templates = {
        name: (ROOT / "templates" / f"{name}.html").read_text(encoding="utf-8")
        for name in ("home", "article", "tag")
    }

    generated = []  # paths written this build, relative to OUT

    def write_page(rel_path: Path, html: str):
        target = OUT / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        generated.append(rel_path.as_posix())

    all_articles = load_articles(ROOT / "articles")
    articles = [a for a in all_articles if not a["draft"]]
    articles.sort(key=date_sort_key, reverse=True)
    tags = sorted({t for a in articles for t in a["tags"]}, key=str.lower)

    base_url = f"https://{site['domain']}/"

    def tag_url(t: str, prefix: str) -> str:
        """URL of a tag archive. prefix = path from the page to site root."""
        return f"{prefix}tag/{tag_slug(t)}/index.html"

    def tag_links(article_tags, prefix: str) -> str:
        """Linked tag pills. prefix = path from the current page to root."""
        return " ".join(
            f'<a class="tag" href="{tag_url(t, prefix)}">{escape(t)}</a>'
            for t in article_tags
        )

    def tag_nav_html(prefix: str, current: str = "") -> str:
        """Row of links to every tag archive (empty string if no tags)."""
        if not tags:
            return ""
        links = []
        for t in tags:
            cur = ' aria-current="page"' if t == current else ""
            links.append(
                f'<a class="tag" href="{tag_url(t, prefix)}"{cur}>{escape(t)}</a>'
            )
        return f'<p class="tags tag-nav">{" ".join(links)}</p>'

    def article_list_html(items, prefix: str) -> str:
        """<ul> of article rows. prefix = path from the page to site root."""
        if not items:
            return f'<p class="section-intro">{blog["empty"]}</p>'
        rows_all = []
        for a in items:
            d = a["date"] or "—"
            rows = [
                "      <li>",
                f'        <p class="meta">{blog["published"]} {d}</p>',
                f'        <h2><a href="{prefix}articles/{a["slug"]}/index.html">{escape(a["title"])}</a></h2>',
                f"        <p>{escape(a['description'])}</p>",
            ]
            if a["tags"]:
                rows.append(
                    f'        <p class="tags">{tag_links(a["tags"], prefix)}</p>'
                )
            rows.append("      </li>")
            rows_all.append("\n".join(rows))
        return '<ul class="article-list">\n' + "\n".join(rows_all) + "\n    </ul>"

    def common_values(depth: int, canonical: str, title: str, description: str) -> dict:
        """Values shared by every page, at a given folder depth.

        depth = number of levels below the site root
        (index.html -> 0, articles/x/index.html -> 2, tag/x/index.html -> 2)
        """
        p = "../" * depth
        return {
            "TITLE": title,
            "DESCRIPTION": description,
            "CANONICAL": canonical,
            "ASSETS": p + "assets",
            "HOME_URL": p + "index.html",
            "BRAND": brand,
            "GITHUB_URL": site["github"],
            "MENU": blog["menu"],
            "NAV_ARTICLES": blog["nav_articles"],
            "THEME_TOGGLE": blog["theme_toggle"],
            "ICON_SUN": ICON_SUN,
            "ICON_MOON": ICON_MOON,
            "YEAR": date.today().year,
            "FOOTER_TAGLINE": blog["footer_tagline"],
            "FOOTER_RIGHTS": blog["footer_rights"],
            "NAV_CURRENT": "",
        }

    # --- home page = article index -----------------------------------------
    values = common_values(0, base_url, site["title"], site["description"])
    values.update(
        {
            "BLOG_LABEL": blog["label"],
            "BLOG_TITLE": blog["title"],
            "BLOG_INTRO": blog["intro"],
            "TAG_NAV": tag_nav_html(""),
            "ARTICLE_LIST": article_list_html(articles, ""),
            "NAV_CURRENT": ' aria-current="page"',
        }
    )
    write_page(Path("index.html"), render(templates["home"], values))

    # --- article pages -------------------------------------------------------
    for a in articles:
        prefix = "../../"
        canonical = f"{base_url}articles/{a['slug']}/"
        values = common_values(
            2,
            canonical,
            f'{escape(a["title"])} — {brand}',
            escape(a["description"]) or site["description"],
        )
        values.update(
            {
                "ARTICLE_DATE": f'{blog["published"]} {a["date"]}',
                "ARTICLE_TITLE": escape(a["title"]),
                "ARTICLE_TAGS": (
                    f'<p class="tags">{tag_links(a["tags"], prefix)}</p>'
                    if a["tags"]
                    else ""
                ),
                "ARTICLE_BODY": a["body"],
            }
        )
        write_page(
            Path("articles") / a["slug"] / "index.html",
            render(templates["article"], values),
        )

    # --- tag archive pages ----------------------------------------------------
    for t in tags:
        tslug = tag_slug(t)
        prefix = "../../"
        tagged = [a for a in articles if t in a["tags"]]
        values = common_values(
            2,
            f"{base_url}tag/{tslug}/",
            f"{escape(t)} — {brand}",
            f'Articles tagged "{t}".',
        )
        values.update(
            {
                "TAG_LABEL": blog["tag_label"],
                "TAG_NAME": escape(t),
                "TAG_NAV": tag_nav_html(prefix, current=t),
                "ARTICLE_LIST": article_list_html(tagged, prefix),
            }
        )
        write_page(
            Path("tag") / tslug / "index.html",
            render(templates["tag"], values),
        )

    # --- sitemap / robots ------------------------------------------------------
    sitemap_urls = [base_url]
    sitemap_urls += [f"{base_url}articles/{a['slug']}/" for a in articles]
    sitemap_urls += [f"{base_url}tag/{tag_slug(t)}/" for t in tags]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in sitemap_urls:
        sitemap += f"  <url><loc>{url}</loc></url>\n"
    sitemap += "</urlset>\n"
    (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    generated.append("sitemap.xml")

    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {base_url}sitemap.xml\n",
        encoding="utf-8",
    )
    generated.append("robots.txt")

    not_found = (
        '<!DOCTYPE html>\n<html lang="en" data-theme="light">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>404 — {brand}</title>\n"
        # root-absolute paths: GitHub serves 404.html for missing URLs at any
        # depth, so relative asset paths would break on nested paths
        '<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">\n'
        '<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">\n'
        '<link rel="stylesheet" href="/assets/style.css">\n'
        '<script>(function(){var t;try{t=localStorage.getItem("farisxdo-theme")}catch(e){}'
        'if(!t){t=window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}'
        'document.documentElement.setAttribute("data-theme",t)})();</script>\n</head>\n<body>\n'
        '<header class="site-header"><div class="wrap header-inner">'
        f'<a class="brand-text" href="/index.html">{brand}</a></div></header>\n'
        '<main><div class="wrap"><p class="breadcrumb"><a href="/index.html">← Home</a></p>'
        '<h1 class="page-title">404</h1>'
        '<p class="section-intro">Page not found.</p></div></main>\n'
        '<script src="/assets/main.js"></script>\n</body>\n</html>\n'
    )
    (OUT / "404.html").write_text(not_found, encoding="utf-8")
    generated.append("404.html")

    # --- assets ------------------------------------------------------------------
    assets_dir = ROOT / "assets"
    for f in sorted(assets_dir.glob("*")):
        if f.is_file():
            target = OUT / "assets" / f.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(f.read_bytes())
            generated.append(f"assets/{f.name}")

    # --- manifest-based cleanup (Windows-safe) ------------------------------------
    stale = []
    if MANIFEST.exists():
        try:
            old = set(json.loads(MANIFEST.read_text(encoding="utf-8")))
        except ValueError:
            old = set()
        for rel in sorted(old - set(generated)):
            p = OUT / rel
            if p.is_file():
                p.unlink()
                stale.append(rel)
            # prune now-empty directories (best effort)
            for parent in [p.parent] + list(p.parents):
                try:
                    if parent != OUT and parent.is_dir() and not any(parent.iterdir()):
                        parent.rmdir()
                except OSError:
                    break
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(sorted(generated), indent=2), encoding="utf-8")

    # --- report ---------------------------------------------------------------------
    print(f"Built {len(generated)} files into site/")
    print(f"  articles published: {len(articles)}")
    print(f"  drafts excluded:    {len(all_articles) - len(articles)}")
    if stale:
        print(f"  removed stale:      {', '.join(stale)}")

    # --- self-check -------------------------------------------------------------------
    problems = []
    for rel in generated:
        if rel.endswith(".html"):
            html_text = (OUT / rel).read_text(encoding="utf-8")
            for src in re.findall(r'(?:href|src)="([^"]+)"', html_text):
                if src.startswith(("http:", "https:", "mailto:", "/")):
                    continue
                path_only = src.split("#")[0]
                if not path_only:
                    continue
                resolved = (OUT / rel).parent / path_only
                if not resolved.exists():
                    problems.append(f"{rel}: missing {src}")
    if problems:
        print("PROBLEMS FOUND:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("Self-check passed: all internal links and assets resolve.")


if __name__ == "__main__":
    build()