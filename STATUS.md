# Project Status
## tech-intel

<!-- DASHBOARD_META
name: tech-intel
slug: tech-intel
status: Active
phase: Phase 3
started: 2026-07-25
last_updated: 2026-07-25
summary: Cloud pipeline live — GitHub Actions + Gemini Flash + Turso. Briefing publishes to GitHub Pages every hour. Next: per-company history mining and knowledge graph.
current_focus: Company 360 Intelligence — seed_company.py (HN history + Wikipedia facts) and ask.py (RAG query CLI)
-->

---

## Current Phase
**Phase 3** — Company Intelligence. Per-company history mining + RAG query interface.

## Status
`Active — cloud pipeline live, company intelligence next`

---

## Current Focus
Build per-company intelligence on top of the live pipeline:
1. `seed_company.py` — cold-start a company: Wikipedia facts + HN Algolia history (2015→now) → Turso
2. `ask.py` — RAG CLI: retrieve signals from Turso → Gemini synthesis → grounded cited answer
3. `company_page.py` — per-company HTML profile → published to GitHub Pages
4. Regional RSS feeds — India (YourStory, Inc42), China (TechNode, 36Kr)
5. Neo4j AuraDB — entity graph (Phase 4, after company intelligence is stable)

---

## What's Built

### Phase 1b — Core Pipeline ✅ (complete, deprecated on Mac)
- APScheduler daemon — ingestion every 30min, briefing every 1h (replaced by GitHub Actions)
- 6 ingestion sources: HackerNews, Reddit, RSS (7 feeds), GitHub Trending, Dev.to
- Ollama + Llama3.2 local classification (replaced by Gemini Flash)
- SQLite schema: signals_raw, signals_enriched, predictions (replaced by Turso)
- `last_shown_at` — 7-day exclusion window prevents signal repetition
- Diversity selection — pool of 60, greedy company-rotation picks 8 per briefing

### Phase 1b — HTML Briefing UI ✅
- Dark theme (#07070d), responsive with clamp() font sizes, 480px mobile breakpoint
- Signal cards: domain-colored left border, entity highlights, company brand badges
- Predictions accordion: resolved (✅/❌) + watching (⏳) — collapsible <details> rows
- Company Watch accordion: 157 companies across 14 categories, 5 real DB signal links per company

### Phase 2 — Cloud Migration ✅ (complete, fully off Mac)
- **Gemini 2.0 Flash** replacing Ollama — batch 5 signals/prompt, ~288 API calls/day (free tier: 1500/day)
- **Turso** (libSQL cloud) replacing SQLite — HTTP API wrapper, zero SQL query changes
- **GitHub Actions** replacing APScheduler daemon:
  - `ingest.yml` — cron every 30min → `ingest_job.py`
  - `briefing.yml` — cron every 1h → `briefing_job.py`
- **GitHub Pages** — briefing auto-published to `mavinash-dev.github.io/tech-intel/` after every run
- Mac Air: zero processes running — only receives Telegram on phone

### Schema ✅
- `signals_raw` — source, source_id (dedup), title, url, body, published_at, processed
- `signals_enriched` — domain, relevance_score, plain_explanation, entities_json, prediction, last_shown_at
- `predictions` — prediction_text, domain, status (watching/confirmed/wrong/expired), signal_id
- `company_facts` — company, fact_type, value, source, as_of (seeded by seed_company.py)

---

## Phase 3 — Company Intelligence Task List

### Step 1 — seed_company.py 🔄 (next)
- [ ] Wikipedia API → infobox extraction → company_facts table
- [ ] HN Algolia API → paginate 2015→now for company name → signals_raw (source="seed_hn")
- [ ] arXiv API → papers mentioning company → signals_raw (source="seed_arxiv")
- [ ] Batch-classify historical signals via Gemini (same classifier, same schema)
- [ ] CLI: `python3 seed_company.py "Nvidia"`
- [ ] Output: "Nvidia: 47 facts stored, 1,847 historical signals seeded (2015–2026)"

### Step 2 — ask.py
- [ ] Parse company name + question from CLI args
- [ ] Retrieve from Turso: top 25 signals mentioning company + company_facts + predictions
- [ ] Format numbered context block
- [ ] Send to Gemini: "answer only from these signals, cite signal numbers"
- [ ] Print grounded answer with citations
- [ ] CLI: `python3 ask.py "What has Anthropic been doing with safety research?"`

### Step 3 — company_page.py
- [ ] Generate per-company HTML profile page
- [ ] Sections: Facts, Signal Timeline, Domain Breakdown, Co-occurring Entities, Prediction History, Strategic Question
- [ ] Output: `docs/companies/{slug}.html`
- [ ] Published automatically to GitHub Pages
- [ ] Company Watch accordion in briefing links to this page when it exists

### Step 4 — Regional RSS feeds
- [ ] YourStory RSS (`yourstory.com/feed`) — India
- [ ] Inc42 RSS (`inc42.com/feed`) — India
- [ ] TechNode RSS (`technode.com/feed`) — China
- [ ] 36Kr English RSS — China
- [ ] 3-line addition in `ingestion/rss.py` per feed

### Step 5 — Replace Product Hunt (broken)
- [ ] Product Hunt GraphQL returns 403
- [ ] Candidates: Lobste.rs API, IndieHackers RSS, BetaList RSS

---

## Phase 4 — Knowledge Graph (planned)

### Neo4j AuraDB (free tier: 200MB)
- [ ] Nodes: Company, Person, Technology, Country, Organization
- [ ] Relationships: SIGNAL (type, date, domain, summary, source_url)
- [ ] Write entities from entities_json → Neo4j on each classification
- [ ] Query: "show me everything connected to Nvidia in the last 90 days"
- [ ] Canonical entity resolution needed first (see ARCH.md §9)

---

## Pending (Post-Phase 3)

### Phase 1c — Web UI (Next.js)
- [ ] Not started — deprioritised until company intelligence complete

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

### 2026-07-25 — Session 5: Cloud Migration Design + Docs
- Decision: move entire pipeline off Mac
- Chose GitHub Actions (public repo = unlimited free minutes) over Fly.io/Railway
- Chose Gemini 2.0 Flash over Groq/Llama — better quality, 1500 req/day free
- Batch classification design: 5 signals/prompt → 288 calls/day (vs 1,440 single)
- Chose Turso over Supabase — libSQL dialect = zero SQL query changes from SQLite
- Documented full migration plan in ARCH.md v0.2
- docs/company-intelligence.md created — RAG design, seed_company.py, ask.py protocol

### 2026-07-25 — Session 6: Cloud Migration Build
- Gemini 2.0 Flash classifier: classifier/gemini_classifier.py (batch 5/prompt)
- Turso HTTP API wrapper: db/connection.py (libsql:// → https://, sqlite3-compatible interface)
- briefing/generator.py: _ollama() → _gemini() using google.genai SDK
- ingest_job.py + briefing_job.py: standalone single-run scripts for GitHub Actions
- .github/workflows/ingest.yml (cron */30) + briefing.yml (cron 0 *)
- GitHub Pages: briefing auto-published to mavinash-dev.github.io/tech-intel/ each run
- db/schema.py: executescript() → per-statement execute() for Turso compat
- Fixed: libsql:// URL scheme, google.generativeai → google.genai (deprecated SDK)
- requirements.txt: removed APScheduler + ollama, added google-genai

---

## Blockers
- Reddit creds not in GitHub Secrets (minor — Reddit is optional)
- Product Hunt: 403 (needs replacement source)
- Need to enable GitHub Pages in repo settings (Settings → Pages → main / /docs)

---

## Live URLs
- **Briefing:** https://mavinash-dev.github.io/tech-intel/ (updates every hour)
- **Repo:** https://github.com/mavinash-dev/tech-intel
- **Actions:** https://github.com/mavinash-dev/tech-intel/actions

---

## Time Tracker

| Date | Session | Hours | Cumulative |
|---|---|---|---|
| 2026-07-25 | Brainstorm + Foundation | 1h | 1h |
| 2026-07-25 | Phase 1a + 1b full build | 4h | 5h |
| 2026-07-25 | UI iteration | 2h | 7h |
| 2026-07-25 | Company watch + intelligence design | 2h | 9h |
| 2026-07-25 | Cloud migration design + docs | 1h | 10h |
| 2026-07-25 | Cloud migration build + fixes | 2h | 12h |

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
| 2026-07-25 | GitHub Pages for briefing | Permanent shareable URL, no auth needed, auto-updates every hour |
| 2026-07-25 | google.genai over google.generativeai | Old SDK deprecated July 2025, new SDK is google-genai package |
| 2026-07-25 | Turso HTTP API over libsql-client | requests already in deps, no SDK version churn, same reliability |
