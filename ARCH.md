# Architecture Document
## tech-intel

**Version:** 0.2 — Cloud migration (GitHub Actions + Gemini + Turso)
**Created:** 2026-07-25
**Updated:** 2026-07-25

---

## 1. Tech Stack

### Current (Phase 1b — local Mac, being migrated away from)
| Layer | Technology | Status |
|---|---|---|
| Ingestion daemon | Python + APScheduler on Mac | → replacing with GitHub Actions |
| Database | SQLite local file | → replacing with Turso |
| AI classification | Ollama + Llama 3.2 (local) | → replacing with Gemini Flash API |
| Briefing generation | Ollama + Llama 3.2 (local) | → replacing with Gemini Flash API |
| Notifications | Telegram Bot API | ✅ keeping |
| Process management | launchd (macOS) | → dropping entirely |

### Target (Phase 2 — fully off Mac)
| Layer | Technology | Reason |
|---|---|---|
| Scheduler / compute | **GitHub Actions** (cron) | Free unlimited on public repo, no VM to manage, UI logs |
| Database | **Turso** (libSQL cloud) | SQLite-compatible, free 500MB, minimal code change |
| AI — classification | **Gemini 2.0 Flash** (Google free tier) | Better quality than Llama 3.2, 1500 req/day free |
| AI — briefing gen | **Gemini 2.0 Flash** (Google free tier) | Same model, consistent quality |
| Notifications | Telegram Bot API | Free, unchanged |
| Mac | Nothing running | Just receives Telegram on phone |

---

## 2. Architecture Overview

### Target Architecture (Phase 2 — fully cloud)
```
┌─────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS                        │
│                                                         │
│  ┌─────────────────────────────────────────┐            │
│  │  ingest.yml  (cron: every 30 min)       │            │
│  │                                         │            │
│  │  fetch HN, RSS, GitHub, Dev.to          │            │
│  │       │                                 │            │
│  │       ▼                                 │            │
│  │  Gemini Flash  ←── batch classify ──→   │            │
│  │  (5 signals per prompt)                 │            │
│  │       │                                 │            │
│  │       ▼                                 │            │
│  │    Turso DB (libSQL cloud)              │            │
│  └─────────────────────────────────────────┘            │
│                                                         │
│  ┌─────────────────────────────────────────┐            │
│  │  briefing.yml  (cron: every 1 hour)     │            │
│  │                                         │            │
│  │  load top signals from Turso            │            │
│  │       │                                 │            │
│  │       ▼                                 │            │
│  │  Gemini Flash  ←── generate briefing    │            │
│  │  (why it matters, question, predictions)│            │
│  │       │                                 │            │
│  │       ▼                                 │            │
│  │  send HTML to Telegram                  │            │
│  └─────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘

GitHub Secrets:
  GEMINI_API_KEY
  TURSO_DATABASE_URL
  TURSO_AUTH_TOKEN
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
  REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET  (optional)
```

### Previous Architecture (Phase 1b — local Mac, deprecated)
```
Mac Air → APScheduler daemon → Ollama → SQLite → Telegram
```

---

## 3. Data Model

### Turso (libSQL) — identical schema to SQLite, same queries

#### signals_raw
```sql
CREATE TABLE IF NOT EXISTS signals_raw (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source       TEXT NOT NULL,
    source_id    TEXT NOT NULL,
    title        TEXT NOT NULL,
    url          TEXT,
    body         TEXT,
    published_at DATETIME,
    ingested_at  DATETIME DEFAULT (datetime('now')),
    processed    BOOLEAN DEFAULT FALSE,
    UNIQUE(source, source_id)
);
```

#### signals_enriched
```sql
CREATE TABLE IF NOT EXISTS signals_enriched (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_id            INTEGER NOT NULL REFERENCES signals_raw(id),
    domain            TEXT NOT NULL,
    relevance_score   REAL NOT NULL,
    plain_explanation TEXT NOT NULL,
    entities_json     TEXT NOT NULL,
    prediction        TEXT,
    enriched_at       DATETIME DEFAULT (datetime('now')),
    last_shown_at     DATETIME   -- NULL until first briefing; 7-day exclusion window prevents repeats
);
```

#### predictions
```sql
CREATE TABLE IF NOT EXISTS predictions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    made_at          DATETIME DEFAULT (datetime('now')),
    briefing_date    DATE NOT NULL,
    prediction_text  TEXT NOT NULL,
    related_entities TEXT,
    domain           TEXT,
    status           TEXT DEFAULT 'watching',  -- watching / confirmed / wrong / expired
    resolved_at      DATETIME,
    resolution_note  TEXT,
    signal_id        INTEGER REFERENCES signals_enriched(id)
);
```

#### company_facts (planned — Phase 2 Company 360)
```sql
CREATE TABLE IF NOT EXISTS company_facts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company     TEXT NOT NULL,
    fact_type   TEXT NOT NULL,  -- founding / ceo / hq / product / acquisition / funding
    value       TEXT NOT NULL,
    source      TEXT,           -- wikipedia / wikidata / crunchbase_rss
    as_of       DATE,
    seeded_at   DATETIME DEFAULT (datetime('now'))
);
```

---

## 4. Gemini Flash — Classification Design

### Why Batched Classification
Gemini Flash free tier: 1,500 requests/day. Single-signal classification would use ~1,440 calls/day (30 signals × 48 runs). Batching 5 signals per prompt drops this to ~288 classification calls/day.

```
Daily budget (1,500 req/day):
  Classification:  30 signals ÷ 5 per batch = 6 calls × 48 runs = 288 calls
  Why it matters:  8 calls × 24 briefings   = 192 calls
  Question gen:    1 call  × 24 briefings   =  24 calls
  Pred resolution: 1 call  × 24 briefings   =  24 calls
  ─────────────────────────────────────────────────────
  Total:                                    = 528 calls/day  (35% of limit)
```

### Batch Classification Prompt Structure
```
Classify these 5 signals. Return a JSON array with one object per signal, in order.

Signal 1: <title> — <body>
Signal 2: <title> — <body>
...

Each object must have:
  domain: Capital|Talent|Technology|Power|Infrastructure|Narrative|Security
  relevance_score: float 0-1 (IT sector relevance)
  plain_explanation: string (1-2 sentences, plain language)
  entities_json: [{name, type}] array
  prediction: string (one forward-looking sentence) or null
```

---

## 5. External APIs & Integrations

### Live Ingestion (GitHub Actions)
| Source | Method | Status |
|---|---|---|
| Hacker News Firebase API | REST | ✅ Working |
| Reddit | PRAW OAuth | ⚠️ Needs creds in GitHub Secrets |
| RSS (TechCrunch, MIT Tech Review, arXiv, TLDR, Crunchbase, YC Blog) | feedparser | ✅ Working |
| GitHub Trending | BeautifulSoup scrape | ✅ Working |
| Dev.to API | REST (no key) | ✅ Working |
| Product Hunt | GraphQL | ❌ 403 — needs replacement |
| Gemini Flash | google-generativeai SDK | 🔄 Replacing Ollama |
| Turso | libsql-client Python | 🔄 Replacing SQLite |
| Telegram Bot API | REST | ✅ Working |

### Historical Seeding (planned — seed_company.py)
| Source | Purpose | Notes |
|---|---|---|
| HN Algolia API | Historical HN discussions per company (2006→now) | Free, no key |
| Wikipedia API | Structured company facts | Free |
| Wikidata API | Machine-readable facts with timestamps | Free |
| arXiv API | Research papers mentioning a company | Free |

### Planned Regional RSS
| Region | Source | Companies covered |
|---|---|---|
| India | YourStory RSS, Inc42 RSS | Zepto, CRED, PhonePe, Razorpay |
| China | TechNode RSS, 36Kr English | DeepSeek, BYD, CATL, Meituan |

---

## 6. Company 360 Intelligence Architecture (Planned — Phase 2)

### RAG Design
LLM role = synthesis only. All facts retrieved from Turso, never from LLM memory.

```
Query: "What has Anthropic been doing with safety research?"
  → retrieve signals mentioning Anthropic from Turso
  → retrieve company_facts for Anthropic
  → retrieve predictions related to Anthropic
  → pass all as context to Gemini Flash
  → grounded answer with signal citations
```

### seed_company.py (planned)
```
python3 seed_company.py "Nvidia"
  1. Wikipedia API → infobox → company_facts table
  2. HN Algolia API → 2015→now → signals_raw (source="seed_hn")
  3. Classify historical signals in batches via Gemini
  Result: 10 years of signal in ~3 minutes
```

### ask.py (planned)
```
python3 ask.py "What signals do we have about TSMC capacity expansion?"
  → retrieve top 20 relevant signals from Turso
  → Gemini synthesizes with citations
  → grounded answer printed to terminal
```

---

## 7. Key Technical Decisions

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-25 | SQLite → Turso | libSQL-compatible, free 500MB, zero SQL query changes |
| 2026-07-25 | Ollama → Gemini Flash | Better classification quality, free 1500 req/day, no local GPU needed |
| 2026-07-25 | APScheduler daemon → GitHub Actions | Public repo = unlimited free minutes, built-in logs, no VM |
| 2026-07-25 | Batch 5 signals per Gemini call | Reduces daily API calls from 1,440 to 288 — fits comfortably in free tier |
| 2026-07-25 | RAG over LLM memory for company facts | LLM training data is frozen — retrieve from grounded sources instead |
| 2026-07-25 | HN Algolia as historical seed | Free, unlimited, covers 2006→now, searchable by query + date range |

---

## 8. GitHub Actions Workflow Design

### .github/workflows/ingest.yml
```yaml
name: Signal Ingestion
on:
  schedule:
    - cron: '*/30 * * * *'   # every 30 minutes
  workflow_dispatch:           # manual trigger button in GitHub UI

jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: python ingest_job.py
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          TURSO_DATABASE_URL: ${{ secrets.TURSO_DATABASE_URL }}
          TURSO_AUTH_TOKEN: ${{ secrets.TURSO_AUTH_TOKEN }}
```

### .github/workflows/briefing.yml
```yaml
name: Briefing Generation
on:
  schedule:
    - cron: '0 * * * *'      # every hour
  workflow_dispatch:

jobs:
  briefing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: python briefing_job.py
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          TURSO_DATABASE_URL: ${{ secrets.TURSO_DATABASE_URL }}
          TURSO_AUTH_TOKEN: ${{ secrets.TURSO_AUTH_TOKEN }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

Note: daemon.py (APScheduler) is replaced by two separate job scripts:
- `ingest_job.py` — single ingestion + classification run (no scheduler loop)
- `briefing_job.py` — single briefing generation + send run (no scheduler loop)

---

## 9. Open Technical Questions

- [ ] Turso free tier resets monthly — do we need a migration plan if we exceed 500MB?
- [ ] Should seed_company.py classify historical signals (Gemini cost) or store raw only (free)?
- [ ] For ask.py — keyword search (free) or vector similarity search (needs embedding API)?
- [ ] How to canonicalize entity names ("Microsoft" vs "Microsoft Corp") before graph write?
- [ ] Should company_facts be seeded for all 157 watchlist companies at once or on-demand?
- [ ] Add YourStory/Inc42/TechNode RSS feeds before or after cloud migration?
