# Funded & Found Out 🔍

**Weekly AI marketing report.**
5 newly funded AI companies, graded on their marketing using the CLEAR framework.
Delivered as a LinkedIn carousel PDF every Wednesday.

---

## What It Does

Every Monday, the pipeline:
1. **Discovers** AI/tech companies that raised $5–40M from VC/PE in the past week (DuckDuckGo search)
2. **Qualifies** them with Claude — filters for real companies with clear funding
3. **Analyzes** each website across 5 CLEAR dimensions
4. **Screenshots** key sections of each website
5. **Generates** a 12-slide LinkedIn carousel PDF

Every Wednesday at 5pm, delivery sends it to your email.

---

## The CLEAR Framework

| Letter | Dimension | What we're grading |
|---|---|---|
| **C** | Centricity | Do they lead with the customer or with themselves? |
| **L** | Legibility | Are use cases clear, specific, and actionable? |
| **E** | Edge | Have they explained why they're not just "ChatGPT for X"? |
| **A** | Argument | Have they made a compelling case for why *them*? |
| **R** | Recall | Is the brand sticky and memorable? |

---

## Setup

### 1. Create virtual environment & install deps

```bash
cd /Users/joshmait/Desktop/Claude/funded-and-found-out
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure .env

```bash
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY
```

### 3. Set up Gmail API (one-time)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → Enable **Gmail API**
3. Create **OAuth 2.0 Client ID** (Desktop app) → Download as `auth/client_secrets.json`
4. First time you run `run_delivery.py`, it will open a browser to authorize your Google account

---

## Usage

### Test first (recommended)

```bash
python scripts/test_run.py --url https://cursor.com --name "Cursor" --funding 20
```

Open the PDF in `output/` to verify the format looks right.

### Run the full pipeline (Monday)

```bash
source .venv/bin/activate
python scripts/run_pipeline.py
```

### Send the email (Wednesday)

```bash
source .venv/bin/activate
python scripts/run_delivery.py
```

---

## Cron Schedule (Mac)

Add to your crontab with `crontab -e`:

```cron
# Funded & Found Out
# Run pipeline every Monday at 9am
0 9 * * 1 cd /Users/joshmait/Desktop/Claude/funded-and-found-out && /Users/joshmait/Desktop/Claude/funded-and-found-out/.venv/bin/python scripts/run_pipeline.py >> logs/cron.log 2>&1

# Send email every Wednesday at 5pm
0 17 * * 3 cd /Users/joshmait/Desktop/Claude/funded-and-found-out && /Users/joshmait/Desktop/Claude/funded-and-found-out/.venv/bin/python scripts/run_delivery.py >> logs/cron.log 2>&1
```

**Note:** Your Mac must be awake at those times for cron to fire. If it's often sleeping, consider using launchd or a small cloud server.

---

## File Structure

```
funded-and-found-out/
├── src/
│   ├── discovery/
│   │   ├── searcher.py       ← DuckDuckGo search (timelimit: past week)
│   │   └── qualifier.py      ← Claude filters to $5-40M VC/PE companies
│   ├── analysis/
│   │   ├── scraper.py        ← requests + BeautifulSoup website extraction
│   │   ├── screenshotter.py  ← Playwright screenshots (hero + features)
│   │   └── evaluator.py      ← Claude CLEAR framework scoring
│   ├── report/
│   │   └── generator.py      ← HTML slides → PNG → PDF carousel
│   ├── delivery/
│   │   └── emailer.py        ← Gmail API attachment send
│   └── tracking/
│       └── database.py       ← SQLite (dedup + run history)
├── scripts/
│   ├── run_pipeline.py       ← Full Monday pipeline
│   ├── run_delivery.py       ← Wednesday email send
│   └── test_run.py           ← Single-company test
├── auth/                     ← Gmail credentials (gitignored)
├── output/                   ← Generated PDFs
├── screenshots/              ← Website screenshots (by date)
├── slides/                   ← Individual PNG slides (by date)
├── data/                     ← SQLite database
├── logs/                     ← Pipeline + delivery logs
├── .env                      ← Your secrets (gitignored)
└── requirements.txt
```

---

## Upgrading to SerpAPI

When you want more precise date filtering, add to `.env`:

```
SERPAPI_KEY=your-key-here
```

Then in `src/discovery/searcher.py`, swap the DuckDuckGo calls for SerpAPI with `tbs=qdr:w` (past week). One-line change per query.
