#!/usr/bin/env python3
"""Morning News Dashboard Generator.

Fetches daily news across tech categories using Claude AI with web search,
then generates a beautiful HTML dashboard.
"""

import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

# ─── Configuration ────────────────────────────────────────────────────────────

CATEGORIES = [
    {
        "id": "tech",
        "name": "Tech News",
        "icon": "💻",
        "color": "#3b82f6",
        "query": "latest technology news today product launches breakthroughs",
    },
    {
        "id": "ai",
        "name": "AI & Machine Learning",
        "icon": "🤖",
        "color": "#a855f7",
        "query": "latest artificial intelligence AI machine learning news models research today",
    },
    {
        "id": "space",
        "name": "Space & Astronomy",
        "icon": "🚀",
        "color": "#06b6d4",
        "query": "latest space exploration NASA SpaceX astronomy discoveries news today",
    },
    {
        "id": "gpu",
        "name": "Graphics Cards & Gaming",
        "icon": "🎮",
        "color": "#10b981",
        "query": "latest GPU graphics card NVIDIA AMD gaming hardware performance benchmarks news today",
    },
    {
        "id": "pricing",
        "name": "Pricing & Economy",
        "icon": "💰",
        "color": "#f59e0b",
        "query": "latest consumer electronics prices inflation tariffs deals pricing economy tech news today",
    },
    {
        "id": "bigtech",
        "name": "Big Tech",
        "icon": "🏢",
        "color": "#ef4444",
        "query": "latest Apple Google Microsoft Meta Amazon Alphabet big tech companies earnings announcements news today",
    },
]

# ─── CSS Styles ───────────────────────────────────────────────────────────────

CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --bg: #0d1117;
    --bg-secondary: #161b22;
    --bg-card: #1c2128;
    --bg-card-hover: #21262d;
    --border: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(255, 255, 255, 0.15);
    --text: #e6edf3;
    --text-secondary: #8b949e;
    --text-muted: #6e7681;
    --radius: 12px;
    --shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    --header-h: 64px;
    --nav-h: 50px;
}

html { scroll-behavior: smooth; }

body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, 'Helvetica Neue', sans-serif;
    line-height: 1.6;
    min-height: 100vh;
}

/* ── Header ── */
.site-header {
    position: sticky;
    top: 0;
    z-index: 200;
    height: var(--header-h);
    background: rgba(13, 17, 23, 0.92);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-bottom: 1px solid var(--border);
}

.header-inner {
    max-width: 1440px;
    margin: 0 auto;
    padding: 0 28px;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}

.header-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
}

.brand-icon { font-size: 26px; line-height: 1; }

.brand-text {
    font-size: 17px;
    font-weight: 700;
    letter-spacing: -0.4px;
    background: linear-gradient(135deg, #e6edf3 20%, #8b949e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header-sep {
    width: 1px;
    height: 20px;
    background: var(--border);
    flex-shrink: 0;
}

.header-date {
    font-size: 13px;
    color: var(--text-secondary);
    white-space: nowrap;
}

.header-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}

.gen-badge {
    font-size: 11px;
    color: var(--text-muted);
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 4px 10px;
    white-space: nowrap;
}

/* ── Navigation ── */
.top-nav {
    position: sticky;
    top: var(--header-h);
    z-index: 100;
    height: var(--nav-h);
    background: rgba(22, 27, 34, 0.95);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
    scrollbar-width: none;
}
.top-nav::-webkit-scrollbar { display: none; }

.nav-inner {
    max-width: 1440px;
    margin: 0 auto;
    padding: 0 28px;
    display: flex;
    align-items: center;
    gap: 4px;
    height: 100%;
}

.nav-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    text-decoration: none;
    color: var(--text-secondary);
    font-size: 12.5px;
    font-weight: 500;
    white-space: nowrap;
    border: 1px solid transparent;
    transition: color 0.15s, background 0.15s, border-color 0.15s;
}

.nav-link:hover {
    color: var(--text);
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--border);
}

.nav-link.active {
    color: var(--cat-color, #3b82f6);
    background: color-mix(in srgb, var(--cat-color, #3b82f6) 12%, transparent);
    border-color: color-mix(in srgb, var(--cat-color, #3b82f6) 28%, transparent);
}

.nav-icon { font-size: 15px; }

/* ── Main ── */
.main-content {
    max-width: 1440px;
    margin: 0 auto;
    padding: 56px 28px 80px;
}

/* ── Hero ── */
.hero {
    text-align: center;
    padding: 56px 0 72px;
    position: relative;
    overflow: hidden;
}

.hero::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 600px;
    height: 300px;
    background: radial-gradient(ellipse at center, rgba(59, 130, 246, 0.07) 0%, transparent 70%);
    pointer-events: none;
}

.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-muted);
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 5px 14px;
    margin-bottom: 20px;
}

.hero-title {
    font-size: clamp(2.2rem, 6vw, 4rem);
    font-weight: 800;
    letter-spacing: -1.5px;
    line-height: 1.05;
    background: linear-gradient(160deg, #e6edf3 0%, #8b949e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 16px;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: var(--text-secondary);
    max-width: 480px;
    margin: 0 auto;
    line-height: 1.7;
}

.hero-stats {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 28px;
    margin-top: 32px;
    flex-wrap: wrap;
}

.stat-item {
    text-align: center;
}

.stat-number {
    display: block;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.2;
}

.stat-label {
    font-size: 11px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.stat-divider {
    width: 1px;
    height: 32px;
    background: var(--border);
}

/* ── Category sections ── */
.category-section {
    margin-bottom: 72px;
    scroll-margin-top: calc(var(--header-h) + var(--nav-h) + 24px);
    opacity: 0;
    animation: fadeInUp 0.45s ease forwards;
}

.category-section:nth-child(1) { animation-delay: 0.05s; }
.category-section:nth-child(2) { animation-delay: 0.10s; }
.category-section:nth-child(3) { animation-delay: 0.15s; }
.category-section:nth-child(4) { animation-delay: 0.20s; }
.category-section:nth-child(5) { animation-delay: 0.25s; }
.category-section:nth-child(6) { animation-delay: 0.30s; }

.category-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 24px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
    position: relative;
}

.category-header::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 64px;
    height: 2px;
    background: var(--cat-color);
    border-radius: 2px;
    transition: width 0.3s;
}

.category-section:hover .category-header::after {
    width: 120px;
}

.category-icon-wrap {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    background: color-mix(in srgb, var(--cat-color) 14%, transparent);
    border: 1px solid color-mix(in srgb, var(--cat-color) 25%, transparent);
    flex-shrink: 0;
}

.category-title {
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.4px;
    color: var(--text);
    flex: 1;
}

.story-count-badge {
    font-size: 11.5px;
    color: var(--text-muted);
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 4px 12px;
    font-weight: 500;
    white-space: nowrap;
}

/* ── Stories grid ── */
.stories-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
    gap: 18px;
}

/* ── Story card ── */
.story-card {
    position: relative;
    border-radius: var(--radius);
    background: var(--bg-card);
    border: 1px solid var(--border);
    overflow: hidden;
    transition: transform 0.18s, border-color 0.18s, box-shadow 0.18s, background 0.18s;
}

.story-card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--radius);
    padding: 1px;
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--cat-color) 25%, transparent) 0%,
        transparent 60%
    );
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    opacity: 0;
    transition: opacity 0.18s;
    pointer-events: none;
}

.story-card:hover {
    background: var(--bg-card-hover);
    border-color: var(--border-hover);
    transform: translateY(-3px);
    box-shadow: var(--shadow), 0 0 0 1px color-mix(in srgb, var(--cat-color) 20%, transparent);
}

.story-card:hover::before { opacity: 1; }

.cat-stripe {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: var(--cat-color);
    opacity: 0.65;
    transition: opacity 0.18s;
}

.story-card:hover .cat-stripe { opacity: 1; }

.story-card-body {
    padding: 18px 20px 16px 22px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    height: 100%;
}

.story-headline {
    font-size: 0.97rem;
    font-weight: 600;
    line-height: 1.45;
    color: var(--text);
    letter-spacing: -0.15px;
}

.story-summary {
    font-size: 0.85rem;
    color: var(--text-secondary);
    line-height: 1.65;
    flex: 1;
}

.story-insight {
    display: flex;
    gap: 9px;
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 9px 11px;
    align-items: flex-start;
}

.insight-icon {
    font-size: 13px;
    flex-shrink: 0;
    margin-top: 2px;
    opacity: 0.85;
}

.insight-text {
    font-size: 0.78rem;
    color: var(--text-secondary);
    line-height: 1.55;
    font-style: italic;
}

.story-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-top: 10px;
    margin-top: 2px;
    border-top: 1px solid var(--border);
}

.source-tag {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--cat-color);
    background: color-mix(in srgb, var(--cat-color) 10%, transparent);
    border: 1px solid color-mix(in srgb, var(--cat-color) 22%, transparent);
    border-radius: 20px;
    padding: 3px 10px;
    letter-spacing: 0.1px;
    text-transform: uppercase;
    font-size: 10px;
}

.no-stories {
    grid-column: 1 / -1;
    text-align: center;
    padding: 40px;
    color: var(--text-muted);
    font-style: italic;
    font-size: 0.9rem;
    background: var(--bg-card);
    border: 1px dashed var(--border);
    border-radius: var(--radius);
}

/* ── Footer ── */
.site-footer {
    border-top: 1px solid var(--border);
    padding: 36px 28px;
    margin-top: 0;
}

.footer-inner {
    max-width: 1440px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    text-align: center;
}

.footer-logo {
    font-size: 20px;
    margin-bottom: 4px;
}

.footer-text {
    font-size: 13px;
    color: var(--text-muted);
}

.footer-disclaimer {
    font-size: 11px;
    color: var(--text-muted);
    opacity: 0.55;
    max-width: 480px;
    line-height: 1.6;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

/* ── Animations ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Responsive ── */
@media (max-width: 900px) {
    .stories-grid { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
}

@media (max-width: 640px) {
    .main-content { padding: 32px 16px 64px; }
    .header-inner { padding: 0 16px; }
    .header-date, .header-sep { display: none; }
    .nav-inner { padding: 0 16px; }
    .stories-grid { grid-template-columns: 1fr; }
    .hero { padding: 36px 0 48px; }
    .hero-title { font-size: 2rem; }
    .hero-stats { gap: 20px; }
    .stat-divider { display: none; }
    .gen-badge { display: none; }
}
"""

JS = """
// Active nav on scroll
const sections = document.querySelectorAll('.category-section[id]');
const navLinks = document.querySelectorAll('.nav-link[data-section]');

const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
        if (e.isIntersecting) {
            navLinks.forEach(l => l.classList.remove('active'));
            const link = document.querySelector(`.nav-link[data-section="${e.target.id}"]`);
            if (link) link.classList.add('active');
        }
    });
}, { threshold: 0.25, rootMargin: '-80px 0px -60% 0px' });

sections.forEach(s => io.observe(s));

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
        e.preventDefault();
        const target = document.querySelector(a.getAttribute('href'));
        if (target) target.scrollIntoView({ behavior: 'smooth' });
    });
});
"""

# ─── News Fetching ─────────────────────────────────────────────────────────────


def fetch_news_for_category(client: anthropic.Anthropic, category: dict) -> list[dict]:
    """Call Claude with web search to get news stories for a category."""
    today = datetime.now().strftime("%B %d, %Y")

    try:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2048,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Today is {today}. Search the web for the most important and recent {category['name']} "
                        f"stories from today or the past 48 hours. Use this search focus: {category['query']}\n\n"
                        "Find the 4-5 most significant stories. For each story provide:\n"
                        "- headline: A clear, specific, factual headline (not vague or generic)\n"
                        "- summary: 2-3 sentences with specific facts, numbers, names, and context\n"
                        "- significance: One concise sentence explaining why this matters to readers\n"
                        "- source: The publication or news source name\n\n"
                        "Respond with ONLY valid JSON in this exact format (no other text):\n"
                        '{"stories": [{"headline": "...", "summary": "...", "significance": "...", "source": "..."}]}'
                    ),
                }
            ],
        )

        # Extract text from all content blocks
        text = ""
        for block in response.content:
            if hasattr(block, "text") and block.text:
                text += block.text

        # Try to parse JSON from the response
        match = re.search(r'\{[\s\S]*"stories"[\s\S]*\}', text)
        if match:
            data = json.loads(match.group())
            return data.get("stories", [])

        # Fallback: try parsing the whole text as JSON
        data = json.loads(text.strip())
        return data.get("stories", [])

    except (json.JSONDecodeError, KeyError, anthropic.APIError) as exc:
        print(f"  Warning: failed to parse response for {category['name']}: {exc}", file=sys.stderr)
        return []
    except Exception as exc:
        print(f"  Error fetching {category['name']}: {exc}", file=sys.stderr)
        return []


# ─── HTML Building ─────────────────────────────────────────────────────────────


def e(text: str) -> str:
    """HTML-escape a string."""
    return html.escape(str(text), quote=True)


def build_story_card(story: dict, color: str) -> str:
    headline = e(story.get("headline", "Untitled"))
    summary = e(story.get("summary", ""))
    significance = story.get("significance", "").strip()
    source = e(story.get("source", "Unknown"))

    insight_html = ""
    if significance:
        insight_html = f"""
            <div class="story-insight">
                <span class="insight-icon">💡</span>
                <p class="insight-text">{e(significance)}</p>
            </div>"""

    return f"""
        <article class="story-card" style="--cat-color: {color}">
            <div class="cat-stripe"></div>
            <div class="story-card-body">
                <h3 class="story-headline">{headline}</h3>
                <p class="story-summary">{summary}</p>
                {insight_html}
                <div class="story-footer">
                    <span class="source-tag">{source}</span>
                </div>
            </div>
        </article>"""


def build_category_section(category: dict, stories: list) -> str:
    color = category["color"]
    icon = category["icon"]
    name = e(category["name"])
    cat_id = category["id"]

    if stories:
        cards = "\n".join(build_story_card(s, color) for s in stories)
        count_label = f"{len(stories)} stories"
    else:
        cards = '<p class="no-stories">No stories could be retrieved for this category.</p>'
        count_label = "0 stories"

    return f"""
    <section class="category-section" id="{cat_id}" style="--cat-color: {color}">
        <div class="category-header">
            <div class="category-icon-wrap">{icon}</div>
            <h2 class="category-title">{name}</h2>
            <span class="story-count-badge">{count_label}</span>
        </div>
        <div class="stories-grid">
            {cards}
        </div>
    </section>"""


def build_nav(categories: list) -> str:
    links = "\n".join(
        f'<a href="#{c["id"]}" class="nav-link" data-section="{c["id"]}" style="--cat-color: {c["color"]}">'
        f'<span class="nav-icon">{c["icon"]}</span><span>{e(c["name"])}</span></a>'
        for c in categories
    )
    return f'<nav class="top-nav" aria-label="News categories"><div class="nav-inner">{links}</div></nav>'


def build_html(all_news: dict, generated_at: datetime, categories: list) -> str:
    date_str = generated_at.strftime("%A, %B %d, %Y")
    time_str = generated_at.strftime("%I:%M %p UTC")
    total_stories = sum(len(v) for v in all_news.values())
    total_categories = sum(1 for k, v in all_news.items() if v)

    sections = "\n".join(
        build_category_section(cat, all_news.get(cat["id"], []))
        for cat in categories
    )

    nav = build_nav(categories)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Daily tech news briefing for {date_str}">
    <title>Morning Briefing — {date_str}</title>
    <style>{CSS}</style>
</head>
<body>

<header class="site-header">
    <div class="header-inner">
        <div style="display:flex;align-items:center;gap:16px;">
            <a href="#" class="header-brand">
                <span class="brand-icon">☀️</span>
                <span class="brand-text">Morning Briefing</span>
            </a>
            <div class="header-sep"></div>
            <span class="header-date">{date_str}</span>
        </div>
        <div class="header-meta">
            <span class="gen-badge">Generated {time_str}</span>
        </div>
    </div>
</header>

{nav}

<main class="main-content">

    <div class="hero">
        <div class="hero-eyebrow">
            <span>📰</span>
            <span>Daily Digest</span>
        </div>
        <h1 class="hero-title">Your Morning Briefing</h1>
        <p class="hero-subtitle">Everything important in tech, AI, space, hardware, and business — summarized.</p>
        <div class="hero-stats">
            <div class="stat-item">
                <span class="stat-number">{total_stories}</span>
                <span class="stat-label">Stories</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
                <span class="stat-number">{total_categories}</span>
                <span class="stat-label">Categories</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
                <span class="stat-number">{generated_at.strftime("%-I%p").lower()}</span>
                <span class="stat-label">Generated</span>
            </div>
        </div>
    </div>

    {sections}

</main>

<footer class="site-footer">
    <div class="footer-inner">
        <div class="footer-logo">☀️</div>
        <p class="footer-text">Morning Briefing · {date_str} · Generated at {time_str}</p>
        <p class="footer-disclaimer">
            Summaries are AI-generated from live web searches. Always verify important information with original sources.
        </p>
    </div>
</footer>

<script>{JS}</script>
</body>
</html>"""


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    now = datetime.now(tz=timezone.utc)
    print(f"Morning Briefing Generator — {now.strftime('%A, %B %d, %Y at %H:%M UTC')}")
    print("=" * 60)

    all_news: dict[str, list] = {}
    for category in CATEGORIES:
        print(f"  Fetching: {category['icon']} {category['name']} ...", end=" ", flush=True)
        stories = fetch_news_for_category(client, category)
        all_news[category["id"]] = stories
        print(f"{len(stories)} stories")

    total = sum(len(v) for v in all_news.values())
    print(f"\n  Total: {total} stories across {len(CATEGORIES)} categories")

    print("\n  Generating HTML dashboard ...", end=" ", flush=True)
    output_html = build_html(all_news, now, CATEGORIES)

    output_path = Path(__file__).parent.parent / "output" / "dashboard.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_html, encoding="utf-8")
    print(f"done\n  Saved to: {output_path}")


if __name__ == "__main__":
    main()
