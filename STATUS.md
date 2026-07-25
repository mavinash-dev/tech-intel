# Project Status
## tech-intel

<!-- DASHBOARD_META
name: tech-intel
slug: tech-intel
status: Active
phase: Phase 2
started: 2026-07-25
last_updated: 2026-07-25
summary: Cloud migration in progress — moving from local Mac daemon (Ollama + SQLite) to GitHub Actions + Gemini Flash + Turso. Zero Mac dependency on completion.
current_focus: Cloud migration — Gemini swap → Turso DB → GitHub Actions workflows
-->

---

## Current Phase
**Phase 2** — Cloud migration. Moving entire pipeline off Mac Air.

## Status
`Active — migration in progress`

---

## Current Focus
Migrating from local Mac stack to fully cloud-hosted pipeline:
1. Replace Ollama → Gemini 2.0 Flash API (batch classification)
2. Replace SQLite → Turso (libSQL-compatible cloud DB)
3. Replace APScheduler daemon → GitHub Actions cron workflows
4. Replace ingest_job.py + briefing_job.py as standalone scripts (no scheduler loop)

---

## What's Built (Phase 1b — complete, running on Mac)

### Core Pipeline ✅
- APScheduler daemon — ingestion every 30min, briefing every 1h
- 6 ingestion sources: HackerNews, Reddit (needs creds), RSS (7 feeds), GitHub Trending, Dev.to, Product Hunt (403 — broken)
- Ollama + Llama3.2 local classification — domain, relevance_score, plain_explanation, entities_json, prediction
- SQLite schema: signals_raw, signals_enriched, predictions — WAL mode, dedup via UNIQUE(source, source_id)
- `last_shown_at` column — 7-day exclusion window prevents signal repetition
- Diversity selection — pool of 60, greedy company-rotation picks 8 per briefing

### HTML Briefing UI ✅
- Dark theme (#07070d), responsive with clamp() font sizes, mobile breakpoint at 480px
- Signal cards: domain-colored left border, entity/number highlights, company brand badges, prediction cross-reference
- Predictions accordion: resolved (✅/❌) + watching (⏳) — collapsible <details> rows
- Company Watch accordion: 157 companies across 14 categories, click → 5 real DB signal links per company

### Company Watch ✅
- 157 companies across 14 categories: US Big Tech, AI/LLM, Cloud/Infra, DevOps/Platform, Observability, Security, Data/Analytics, SaaS/Enterprise, Fintech/Crypto, Hardware/Transport, China, Korea/Taiwan/Japan, Europe, India, Semiconductor

---

## Phase 2 Migration — Task List

### Step 1 — Gemini Flash swap 🔄 (next)
- [ ] Add `google-generativeai` to requirements.txt
- [ ] Rewrite `classifier/gemini_classifier.py` — batch 5 signals per prompt
- [ ] Update `briefing/generator.py` — replace `_ollama()` with `_gemini()`
- [ ] Update `config.py` — GEMINI_API_KEY instead of OLLAMA_HOST/MODEL
- [ ] Test locally with real Gemini API key before touching DB

### Step 2 — Turso DB swap
- [ ] Create Turso account + database
- [ ] Add `libsql-client` to requirements.txt
- [ ] Rewrite `db/connection.py` — libsql HTTP client instead of sqlite3
- [ ] Run `db/schema.py` against Turso to create tables
- [ ] Migrate existing local signals to Turso (optional — can start fresh)
- [ ] Verify all SQL queries work unchanged

### Step 3 — GitHub Actions workflows
- [ ] Create `ingest_job.py` — single ingestion + classification run (no scheduler)
- [ ] Create `briefing_job.py` — single briefing gen + Telegram send (no scheduler)
- [ ] Create `.github/workflows/ingest.yml` — cron every 30min
- [ ] Create `.github/workflows/briefing.yml` — cron every 1h
- [ ] Add all secrets to GitHub repo settings:
  - GEMINI_API_KEY
  - TURSO_DATABASE_URL
  - TURSO_AUTH_TOKEN
  - TELEGRAM_BOT_TOKEN
  - TELEGRAM_CHAT_ID
- [ ] Test manual workflow_dispatch trigger
- [ ] Verify end-to-end: ingest → classify → Turso → briefing → Telegram

### Step 4 — Cleanup
- [ ] Stop local daemon on Mac
- [ ] Archive daemon.py (keep for reference)
- [ ] Remove Ollama dependency from requirements.txt
- [ ] Update README with new setup instructions (no Ollama, no local DB)

---

## Pending (Post-Migration)

### Company 360 Intelligence
- [ ] `seed_company.py` — HN Algolia (2015→now) + Wikipedia facts → Turso
- [ ] `ask.py` — RAG CLI: retrieve signals → Gemini synthesis → cited answer
- [ ] Expand sources: YourStory/Inc42 (India), TechNode (China)
- [ ] Replace Product Hunt (403) with alternative

### Phase 1c — Web UI (Next.js)
- [ ] Not started — deprioritised until cloud migration complete

### Phase 1d — Neo4j Graph
- [ ] Not started — may become cloud Neo4j AuraDB (free tier: 200MB)

---

## Development Log

### 2026-07-25 — Session 1: Foundation
- Full brainstorm, system design, project docs created
- GitHub repo initialized: mavinash-dev/tech-intel

### 2026-07-25 — Session 2: Full Phase 1a + 1b Build
- Built entire ingestion pipeline (6 sources), Ollama classifier, APScheduler daemon
- Built briefing generator, Telegram delivery, HTML formatter
- Fixes: Python 3.9 type hints, UTC/IST timezone offset, Telegram data= vs json=, hex opacity bug
- 18/18 smoke tests passing

### 2026-07-25 — Session 3: UI Iteration
- Multiple HTML briefing rounds: domain colors, company brand colors, watch section
- Switched to HTML sendDocument to bypass Telegram formatting limits

### 2026-07-25 — Session 4: Company Watch + Intelligence Design
- Watchlist 12 → 157 companies across 14 global categories
- Company watch → clickable accordion with real DB signal links
- Predictions accordion — same <details> pattern
- Signal dedup: last_shown_at column, 7-day exclusion, pool of 60
- Responsive UI: clamp() font sizes, 480px mobile breakpoint
- send_now.py now runs ingestion before briefing

### 2026-07-25 — Session 5: Cloud Migration Design
- Decision: move entire pipeline off Mac
- Chose GitHub Actions (public repo = unlimited free minutes) over Fly.io/Railway
- Chose Gemini 2.0 Flash over Groq/Llama — better quality, 1500 req/day free
- Batch classification design: 5 signals/prompt → 288 calls/day (vs 1,440 single)
- Chose Turso over Supabase — libSQL compatible, zero SQL query changes
- Documented full migration plan in ARCH.md v0.2

---

## Blockers
- Reddit creds not in .env (minor — Reddit is optional)
- Product Hunt: 403 (needs replacement source)
- Gemini API key: need to create at aistudio.google.com
- Turso: need to create account at turso.tech

---

## Time Tracker

| Date | Session | Hours | Cumulative |
|---|---|---|---|
| 2026-07-25 | Brainstorm + Foundation | 1h | 1h |
| 2026-07-25 | Phase 1a + 1b full build | 4h | 5h |
| 2026-07-25 | UI iteration | 2h | 7h |
| 2026-07-25 | Company watch + intelligence design | 2h | 9h |
| 2026-07-25 | Cloud migration design + docs | 1h | 10h |

---

## Key Decisions Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-25 | Ollama-only for Phase 1 | No API key needed, fully free and local |
| 2026-07-25 | SQLite before Neo4j | Zero-config start |
| 2026-07-25 | Telegram sendDocument | Bypasses 4096 char limit and HTML parse mode |
| 2026-07-25 | Migrate off Mac entirely | Mac Air shouldn't need to run for intelligence pipeline |
| 2026-07-25 | GitHub Actions over Fly.io | Public repo = unlimited free minutes, zero infra to manage |
| 2026-07-25 | Gemini Flash over Groq | Better quality classification, 1500 req/day sufficient with batching |
| 2026-07-25 | Batch 5 signals per Gemini call | Reduces daily API calls 5x — fits easily in free tier |
| 2026-07-25 | Turso over Supabase | libSQL dialect = zero SQL query changes from SQLite |
| 2026-07-25 | RAG over LLM memory for company facts | Grounded retrieval beats hallucination-prone training data |
