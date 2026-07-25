# tech-intel — Project Brief for Claude

> Read this first. Every session. This is your full context.

---

## What This Project Is

**One-liner:** A fully cloud-hosted signal intelligence system that ingests global tech signals, classifies them with AI, and delivers analyst-grade HTML briefings via Telegram and a public GitHub Pages URL. Company-specific deep intelligence via historical mining and RAG queries is being built next.

**Problem:** Most tech news is surface-level. The deeper signals — capital flows, talent movements, regulatory shifts, infrastructure control — require cross-domain pattern recognition across time and geography. Avinash has 4 years in the industry but has never followed tech news and is building his understanding from scratch.

**Solution:** GitHub Actions cron jobs ingest from free public APIs every 30 min, Gemini Flash classifies in batches, Turso stores everything, and an HTML briefing is delivered to Telegram + published to GitHub Pages every hour. Nothing runs on Mac.

---

## Target Users

- **Primary:** Avinash — software engineer, 4 years experience, new to global tech ecosystem
- **Secondary:** 2 friends max, shared via Telegram + GitHub Pages URL
- **Not targeting:** Enterprise, public users, paid subscribers

---

## Current Phase & Status

**Phase:** Phase 3 — Company Intelligence
**Status:** Active — cloud pipeline live, building per-company intelligence next

### What's done

**Phase 2 — Cloud migration (complete):**
- GitHub Actions: `ingest.yml` (every 30min) + `briefing.yml` (every 1h)
- Gemini 2.0 Flash classifier: `classifier/gemini_classifier.py` — batch 5 signals/prompt
- Turso (libSQL cloud) DB: `db/connection.py` — HTTP API wrapper, mimics sqlite3 interface
- GitHub Pages: briefing auto-published to `mavinash-dev.github.io/tech-intel/` each run
- Mac Air: zero processes running

**Phase 1b — Core pipeline (complete, now running in cloud):**
- 5 ingestion sources: HN, RSS (7 feeds), GitHub Trending, Dev.to, Reddit (needs creds)
- HTML briefing: dark theme, signal cards, predictions accordion, 157-company watch accordion
- Telegram delivery: sendDocument (HTML file, bypasses 4096 char limit)
- Signal dedup: `last_shown_at` 7-day exclusion window
- Diversity selection: pool of 60, greedy company-rotation picks 8 per briefing

### What's next

**Phase 3 — Company Intelligence:**
1. `seed_company.py` — cold-start per company: Wikipedia facts + HN Algolia history (2015→now) + arXiv → Turso
2. `ask.py` — RAG CLI: retrieve signals from Turso → Gemini synthesis → cited grounded answer
3. `company_page.py` — per-company HTML profile → `docs/companies/{slug}.html` → GitHub Pages
4. Regional RSS: YourStory/Inc42 (India), TechNode/36Kr (China)

**Phase 4 — Knowledge Graph:**
- Neo4j AuraDB (free tier) — entities as nodes, signals as relationships
- Canonical entity resolution before graph writes
- Cypher queries: co-occurrence, signal chains, supply chain traversal

---

## Hard Constraints

- Everything must be free — no paid APIs, no paid hosting
- Nothing runs on Mac Air — full cloud pipeline only
- Gemini Flash free tier: 1500 req/day — batch classification keeps us at ~528/day
- Telegram only (no WhatsApp — paid Meta Business API)
- Max 3 users, no auth complexity
- All secrets in `.env` (local) and GitHub Secrets (cloud) — never in code

---

## Tech Stack

- **Scheduler:** GitHub Actions cron (public repo = unlimited free minutes)
- **AI:** Gemini 2.0 Flash — `google-genai` SDK (NOT `google-generativeai` — that's deprecated)
- **DB:** Turso (libSQL cloud) — HTTP API via `requests`, same SQL dialect as SQLite
- **Ingestion:** feedparser (RSS), requests (HN/GitHub), praw (Reddit), beautifulsoup4 (GitHub Trending)
- **Notifications:** Telegram Bot API (sendDocument for HTML files)
- **Publishing:** GitHub Pages from `docs/` folder on `main` branch
- **Language:** Python 3.11

---

## Key Files

| File | Purpose |
|---|---|
| `ingest_job.py` | Single-run ingestion + classification (called by ingest.yml) |
| `briefing_job.py` | Single-run briefing gen + Telegram send + docs/index.html publish |
| `classifier/gemini_classifier.py` | Gemini batch classifier (5 signals/prompt) |
| `briefing/generator.py` | Loads signals, calls Gemini for why/question/prediction resolution |
| `briefing/html_formatter.py` | Full HTML briefing renderer — 157 companies, signal cards, accordions |
| `briefing/telegram.py` | Telegram sendDocument delivery |
| `db/connection.py` | TursoConnection (HTTP API) + sqlite3 fallback — same interface |
| `db/schema.py` | Table creation — runs per-statement (not executescript) for Turso compat |
| `config.py` | All env vars: GEMINI_API_KEY, TURSO_DATABASE_URL, TURSO_AUTH_TOKEN, TELEGRAM_* |
| `.github/workflows/ingest.yml` | GitHub Actions cron every 30min |
| `.github/workflows/briefing.yml` | GitHub Actions cron every 1h, pushes docs/index.html |
| `docs/index.html` | Latest briefing — auto-committed by briefing.yml, served by GitHub Pages |
| `docs/company-intelligence.md` | Full per-company intelligence protocol (RAG, seed, ask) |

**Planned:**
| File | Purpose |
|---|---|
| `seed_company.py` | Cold-start a company: Wikipedia + HN Algolia + arXiv → Turso |
| `ask.py` | RAG query CLI: grounded answers about a company from DB signals |
| `company_page.py` | Generate per-company HTML profile → docs/companies/{slug}.html |

---

## Data Model Summary

- `signals_raw` — source, source_id (dedup key), title, url, body, published_at, processed
- `signals_enriched` — domain, relevance_score, plain_explanation, entities_json, prediction, last_shown_at
- `predictions` — prediction_text, domain, status (watching/confirmed/wrong/expired), signal_id
- `company_facts` — company, fact_type, value, source, as_of (populated by seed_company.py)

**Domain taxonomy:** Capital / Talent / Technology / Power / Infrastructure / Narrative / Security

---

## Signal Sources

| Source | Status |
|---|---|
| Hacker News Firebase API | ✅ Live |
| RSS: TechCrunch, MIT Tech Review, arXiv, TLDR, Crunchbase, YC Blog (7 feeds) | ✅ Live |
| GitHub Trending (scrape) | ✅ Live |
| Dev.to API | ✅ Live |
| Reddit PRAW | ⚠️ Needs creds in GitHub Secrets |
| Product Hunt | ❌ 403 — needs replacement |
| HN Algolia (historical seed) | 🔄 Planned — seed_company.py |
| Wikipedia API (facts seed) | 🔄 Planned — seed_company.py |
| YourStory / Inc42 RSS (India) | 🔄 Planned |
| TechNode / 36Kr RSS (China) | 🔄 Planned |

---

## Company Watch

157 companies across 14 global categories tracked in `briefing/html_formatter.py`:
- US Big Tech, AI/LLM, Cloud/Infra, DevOps/Platform, Observability, Security
- Data/Analytics, SaaS/Enterprise, Fintech/Crypto, Hardware/Transport
- China, Korea/Taiwan/Japan, Europe, India, Semiconductor

Each company in the briefing accordion shows 5 real DB signal links from `signals_raw`.

---

## Company Intelligence Protocol (RAG — Phase 3)

**Core rule:** LLMs synthesize only. All facts come from Turso, never from LLM training data.

```
seed_company.py "Nvidia"
  → Wikipedia facts → company_facts table
  → HN Algolia 2015→now → signals_raw (source="seed_hn")
  → arXiv papers → signals_raw (source="seed_arxiv")
  → Gemini batch classify → signals_enriched

ask.py "What signals do we have about TSMC capacity constraints?"
  → retrieve 25 signals + company_facts + predictions from Turso
  → Gemini: "answer from context only, cite signal numbers"
  → grounded cited answer
```

Full protocol: `docs/company-intelligence.md`

---

## Live URLs

- **Briefing (GitHub Pages):** https://mavinash-dev.github.io/tech-intel/
- **Repo:** https://github.com/mavinash-dev/tech-intel
- **Actions:** https://github.com/mavinash-dev/tech-intel/actions

---

## How to Continue This Project

1. Read `STATUS.md` → Current Focus + Phase 3 Task List
2. Read `docs/company-intelligence.md` → company intelligence protocol detail
3. Read `ARCH.md` → architecture including graph design
4. Say: "Continuing tech-intel — ready to build [seed_company.py / ask.py / company_page.py]"

---

## Important Context

- Avinash is new to following tech news — explain everything in plain language, define jargon
- Do NOT suggest running anything on Mac — everything is GitHub Actions
- Do NOT suggest paid APIs or paid hosting
- `google-generativeai` is deprecated — always use `google-genai` package and `from google import genai`
- Turso connection uses HTTP API directly via `requests` — NOT libsql-client SDK
- `db/schema.py` uses per-statement `execute()` calls, NOT `executescript()` (Turso has no executescript)
- GitHub Actions briefing workflow has `permissions: contents: write` to push docs/index.html
