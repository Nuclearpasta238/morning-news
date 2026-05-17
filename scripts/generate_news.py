#!/usr/bin/env python3
"""
Morning News Dashboard Generator
- Fetches top stories from RSS feeds across 6 categories
- Generates a beautiful dark-mode HTML dashboard
- POSTs the HTML to a Zapier Webhook → tiiny.host publishes a live URL
- Also saves dashboard.html locally and commits it

Required env vars:
  ZAPIER_WEBHOOK_URL  — from your Zapier "Catch Hook" trigger
"""

import os
import re
import sys
import json
import requests
import feedparser
from datetime import datetime, timezone
from html import escape

# ── Feed sources ──────────────────────────────────────────────────────────────

CATEGORIES = [
    {
        "key":    "tech",
        "icon":   "⚡",
        "label":  "Tech News",
        "accent": "#3b82f6",
        "feeds": [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
        ],
    },
    {
        "key":    "ai",
        "icon":   "🤖",
        "label":  "Artificial Intelligence",
        "accent": "#a855f7",
        "feeds": [
            "https://venturebeat.com/category/ai/feed/",
            "https://www.artificialintelligence-news.com/feed/",
        ],
    },
    {
        "key":    "space",
        "icon":   "🚀",
        "label":  "Space",
        "accent": "#06b6d4",
        "feeds": [
            "https://spacenews.com/feed/",
            "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        ],
    },
    {
        "key":    "gpu",
        "icon":   "🎮",
        "label":  "Graphics Cards & GPUs",
        "accent": "#22c55e",
        "feeds": [
            "https://www.tomshardware.com/rss/news",
            "https://www.guru3d.com/feeds/news",
        ],
    },
    {
        "key":    "pricing",
        "icon":   "💰",
        "label":  "Pricing & Economics",
        "accent": "#f59e0b",
        "feeds": [
            "https://feeds.arstechnica.com/arstechnica/gadgets",
            "https://feeds.arstechnica.com/arstechnica/tech-policy",
        ],
    },
    {
        "key":    "bigtech",
        "icon":   "🏢",
        "label":  "Big Tech",
        "accent": "#f43f5e",
        "feeds": [
            "https://www.cnbc.com/id/19854910/device/rss/rss.html",
            "https://feeds.reuters.com/reuters/technologyNews",
        ],
    },
]

STORIES_PER_CATEGORY = 5

# ── Fetch ─────────────────────────────────────────────────────────────────────

def strip_html(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()


def fetch_stories(feed_urls, count=STORIES_PER_CATEGORY):
    seen = set()
    stories = []
    for url in feed_urls:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "MorningNewsDashboard/1.0"})
            for entry in feed.entries:
                title = strip_html(entry.get("title", "")).strip()
                if not title or title in seen:
                    continue
                seen.add(title)
                raw_summary = (
                    entry.get("summary")
                    or entry.get("description")
                    or entry.get("content", [{}])[0].get("value", "")
                )
                summary = strip_html(raw_summary)
                # Trim to ~280 chars at a word boundary
                if len(summary) > 280:
                    summary = summary[:280].rsplit(" ", 1)[0] + "…"
                stories.append({"title": title, "summary": summary})
                if len(stories) >= count:
                    return stories
        except Exception as exc:
            print(f"  [warn] {url}: {exc}", file=sys.stderr)
    return stories[:count]


# ── HTML generation ───────────────────────────────────────────────────────────

STYLE = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0d0f14;--surface:#161b25;--surface2:#1e2536;--border:#2a3145;
  --text:#e2e8f0;--text-muted:#64748b;--text-dim:#94a3b8;--radius:12px;
}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Inter','Segoe UI',sans-serif;line-height:1.6;min-height:100vh}
header{background:linear-gradient(135deg,#0d0f14 0%,#161b25 100%);border-bottom:1px solid var(--border);padding:2rem 2rem 1.5rem;display:flex;flex-direction:column;align-items:center;gap:.5rem;position:sticky;top:0;z-index:100;backdrop-filter:blur(12px)}
.eyebrow{font-size:.7rem;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:var(--text-muted)}
h1{font-size:clamp(1.4rem,3vw,2rem);font-weight:800;letter-spacing:-.02em;background:linear-gradient(90deg,#e2e8f0 30%,#94a3b8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.meta{display:flex;gap:1.5rem;font-size:.75rem;color:var(--text-muted);flex-wrap:wrap;justify-content:center}
.meta span{display:flex;align-items:center;gap:.3rem}
.live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.3)}}
nav{display:flex;gap:.5rem;flex-wrap:wrap;justify-content:center;padding:1rem 2rem;background:var(--bg);border-bottom:1px solid var(--border)}
.pill{font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;padding:.35rem .9rem;border-radius:999px;border:1px solid var(--border);background:var(--surface);color:var(--text-dim);text-decoration:none;transition:all .2s}
.pill:hover{color:var(--c);border-color:var(--c)}
main{max-width:1400px;margin:0 auto;padding:2rem 1.5rem 4rem;display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:1.5rem}
.cat{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;display:flex;flex-direction:column;transition:border-color .25s}
.cat:hover{border-color:var(--ac)}
.cat-hd{padding:1.1rem 1.25rem .9rem;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:.75rem;background:linear-gradient(90deg,color-mix(in srgb,var(--ac) 8%,transparent),transparent)}
.cat-title{font-size:.75rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--ac)}
.cnt{margin-left:auto;font-size:.65rem;font-weight:600;color:var(--text-muted);background:var(--surface2);padding:.2rem .55rem;border-radius:999px;border:1px solid var(--border)}
.stories{display:flex;flex-direction:column}
.story{padding:1rem 1.25rem;border-bottom:1px solid var(--border);display:grid;grid-template-columns:auto 1fr;gap:.75rem;align-items:start;transition:background .15s}
.story:last-child{border-bottom:none}
.story:hover{background:var(--surface2)}
.num{font-size:.65rem;font-weight:700;color:var(--text-muted);background:var(--surface2);border:1px solid var(--border);border-radius:6px;width:22px;height:22px;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px}
.hl{font-size:.88rem;font-weight:600;color:var(--text);line-height:1.4;margin-bottom:.3rem}
.sm{font-size:.78rem;color:var(--text-dim);line-height:1.55}
footer{text-align:center;padding:2rem;font-size:.72rem;color:var(--text-muted);border-top:1px solid var(--border)}
::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:var(--bg)}::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
"""


def render_category(cat, stories):
    ac = cat["accent"]
    key = cat["key"]
    icon = cat["icon"]
    label = escape(cat["label"])
    count = len(stories)

    story_html = ""
    for i, s in enumerate(stories, 1):
        title = escape(s["title"])
        summary = escape(s["summary"]) if s["summary"] else ""
        story_html += f"""
      <div class="story">
        <div class="num">{i}</div>
        <div>
          <div class="hl">{title}</div>
          {"<div class='sm'>" + summary + "</div>" if summary else ""}
        </div>
      </div>"""

    return f"""
  <section class="cat" id="{key}" style="--ac:{ac}">
    <div class="cat-hd">
      <span style="font-size:1.2rem">{icon}</span>
      <span class="cat-title">{label}</span>
      <span class="cnt">{count} stories</span>
    </div>
    <div class="stories">{story_html}
    </div>
  </section>"""


def generate_html(all_categories, date_str):
    total = sum(len(c["stories"]) for c in all_categories)
    day_label = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")

    nav_pills = "".join(
        f'<a class="pill" href="#{c["key"]}" style="--c:{c["accent"]}">{c["icon"]} {escape(c["label"])}</a>'
        for c in CATEGORIES
    )

    sections = "".join(
        render_category(c, c["stories"]) for c in all_categories
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Morning News — {escape(date_str)}</title>
  <style>{STYLE}</style>
</head>
<body>
<header>
  <div class="eyebrow">Daily Intelligence Brief</div>
  <h1>Morning News Dashboard</h1>
  <div class="meta">
    <span><span class="live"></span> Live</span>
    <span>📅 {escape(day_label)}</span>
    <span>🗂 {len(CATEGORIES)} categories · {total} stories</span>
  </div>
</header>
<nav>{nav_pills}</nav>
<main>{sections}
</main>
<footer>Morning News Dashboard · {escape(date_str)} · Auto-generated via GitHub Actions + Zapier + tiiny.host</footer>
</body>
</html>"""


# ── Zapier webhook ────────────────────────────────────────────────────────────

def post_to_zapier(html: str, webhook_url: str) -> dict:
    print(f"Posting {len(html):,} chars to Zapier…")
    resp = requests.post(
        webhook_url,
        json={"html": html},
        timeout=30,
        headers={"Content-Type": "application/json"},
    )
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"status": resp.text}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    print(f"Generating Morning News Dashboard for {date_str}")

    for cat in CATEGORIES:
        print(f"  Fetching {cat['label']}…")
        cat["stories"] = fetch_stories(cat["feeds"])
        print(f"    → {len(cat['stories'])} stories")

    html = generate_html(CATEGORIES, date_str)

    # Save locally
    os.makedirs("output", exist_ok=True)
    with open("output/dashboard.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved output/dashboard.html")

    # Post to Zapier → tiiny.host
    webhook_url = os.environ.get("ZAPIER_WEBHOOK_URL", "").strip()
    if webhook_url:
        result = post_to_zapier(html, webhook_url)
        print(f"Zapier response: {json.dumps(result, indent=2)}")
    else:
        print("ZAPIER_WEBHOOK_URL not set — skipping live publish")
        print("Tip: add it as a GitHub Actions secret to enable auto-publishing")


if __name__ == "__main__":
    main()
