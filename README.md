# Morning News Dashboard

A daily automated news briefing that fetches the latest stories in tech, AI, space, graphics cards, pricing, and big tech — then renders everything as a beautiful, scrollable HTML dashboard.

## How it works

1. **GitHub Actions** triggers the workflow every day at **6:00 AM UTC**
2. `scripts/fetch_news.py` calls **Claude AI** (claude-opus-4-7) with built-in web search
3. Claude searches for top stories in each of 6 categories
4. The script generates a dark-mode HTML dashboard at `output/dashboard.html`
5. The workflow commits and pushes the updated dashboard automatically

## Categories

| # | Category | Focus |
|---|----------|-------|
| 1 | 💻 Tech News | Product launches, breakthroughs |
| 2 | 🤖 AI & ML | Models, research, industry moves |
| 3 | 🚀 Space & Astronomy | NASA, SpaceX, discoveries |
| 4 | 🎮 Graphics Cards | NVIDIA, AMD, benchmarks |
| 5 | 💰 Pricing & Economy | Consumer prices, inflation, deals |
| 6 | 🏢 Big Tech | Apple, Google, Microsoft, Meta, Amazon |

## Setup

### 1. Add the API key secret

In your GitHub repository, go to **Settings → Secrets and variables → Actions** and add:

| Secret name | Value |
|-------------|-------|
| `ANTHROPIC_API_KEY` | Your key from [console.anthropic.com](https://console.anthropic.com) |

### 2. Enable GitHub Actions

Make sure Actions are enabled for the repository (Settings → Actions → General).

### 3. (Optional) GitHub Pages

To view the dashboard in a browser via GitHub Pages:

1. Go to **Settings → Pages**
2. Set source to **Deploy from a branch**
3. Choose `main` (or your branch) and `/ (root)` or `/output` folder
4. The dashboard will be live at `https://<user>.github.io/<repo>/output/dashboard.html`

### 4. Manual run

Trigger it anytime via **Actions → Daily News Dashboard → Run workflow**.

## Local development

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python scripts/fetch_news.py
open output/dashboard.html
```

## Schedule

The cron expression `0 6 * * *` runs at exactly **06:00 UTC** every day. Adjust in `.github/workflows/daily-news.yml` to match your timezone.

| UTC offset | Local 6 AM runs at UTC |
|------------|------------------------|
| UTC-5 (ET) | 11:00 UTC |
| UTC-8 (PT) | 14:00 UTC |
| UTC+1 (CET)| 05:00 UTC |
