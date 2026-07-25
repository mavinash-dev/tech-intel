# Project Status
## tech-intel

<!-- DASHBOARD_META
name: tech-intel
slug: tech-intel
status: Active
phase: Phase 1b
started: 2026-07-25
last_updated: 2026-07-25
summary: Local signal intelligence system — ingests global tech signals, classifies with Ollama, delivers HTML briefings via Telegram. Company watch with 157 companies across 14 categories. RAG-based company 360 analysis in design.
current_focus: Company 360 architecture design + historical data seeding strategy
-->

---

## Current Phase
**Phase 1b** — Briefing generation, Telegram delivery, and HTML UI complete. Company intelligence layer in design.

## Status
`Active`

---

## Current Focus
Designing company 360 intelligence layer — RAG query interface over grounded historical + live signals. Historical seeding strategy (HN Algolia back to 2015, Wikipedia structured facts) finalized but not yet built.

---

## What's Built (as of 2026-07-25)

### Core Pipeline ✅
- APScheduler daemon — ingestion every 30min, briefing every 1h
- 6 ingestion sources: HackerNews, Reddit (skipped if no creds), RSS (7 feeds), GitHub Trending, Dev.to, Product Hunt (403 — needs replacement)
- Ollama + Llama3.2 local classification — domain, relevance_score, plain_explanation, entities_json, prediction
- SQLite schema: signals_raw, signals_enriched, predictions — WAL mode, dedup via UNIQUE(source, source_id)
- `last_shown_at` column on signals_enriched — prevents same signal appearing in consecutive briefings

### Briefing System ✅
- `briefing/generator.py` — loads top signals (6h window, pool of 40), diversity-selects 8 covering different watchlist companies
- `briefing/telegram.py` — sends text summary (top 3 signals) then HTML file as document
- `briefing/html_formatter.py` — full dark-mode HTML briefing
- `send_now.py` — manual trigger: runs ingestion first, then generates, then sends + opens

### HTML Briefing UI ✅
- Dark theme (#07070d), responsive (`clamp()` font sizes, mobile breakpoint at 480px)
- Signal cards: domain-colored left border, entity highlights (purple), number highlights (green), company brand badges, prediction cross-reference
- Predictions accordion: resolved (✅/❌) + watching (⏳) all in collapsible rows
- Company Watch accordion: 157 companies across 14 categories, click to expand and see up to 5 real DB signal links per company
- Stats header: Surfaced / Ingested (24h) / Tracked / Resolved

### Company Watch ✅
- 157 companies across 14 categories: US Big Tech, AI/LLM, Cloud/Infra, DevOps/Platform, Observability, Security, Data/Analytics, SaaS/Enterprise, Fintech/Crypto, Hardware/Transport, China, Korea/Taiwan/Japan, Europe, India, Semiconductor
- Each company has a brand color for dark-mode visibility
- Active companies (in today's signals) show glowing dot + brand-colored name + signal index reference

---

## Pending / In Design

### Company 360 Intelligence (Designed, Not Built)
**Architecture decision:** RAG over grounded data — never ask LLM for facts from memory.

Three data layers:
1. **Structured facts** (cold start): Wikipedia API + Wikidata → founding, CEO, products, acquisitions, market cap history
2. **Historical signals** (back-window): HN Algolia API (2015→now, free), arXiv papers — gives 10 years of community signal per company
3. **Live pipeline**: existing ingestion (what we have now)

Query interface planned:
- `seed_company.py <CompanyName>` — one-time seed for any company: Wikipedia facts + HN Algolia history → stored in DB
- `ask.py "<question>"` — RAG CLI: retrieves all relevant signals from DB → passes as context to Ollama → grounded answer with citations

**Key insight:** Source coverage depends on company geography. US companies = good HN/RSS coverage. Indian companies need YourStory/Inc42 RSS. Chinese companies need TechNode/36Kr. Coverage must match company's ecosystem.

### Source Expansion Needed
- Indian tech: YourStory RSS, Inc42 RSS
- Chinese tech: TechNode RSS, 36Kr English
- Replace Product Hunt (403 error) with alternative
- Reddit creds still not configured

### launchd plist
- Mac auto-start on reboot — not yet built

### Phase 1c — Web UI
- Next.js app (localhost:3000) — not started
- Endpoints: /signals, /briefing, /entity, /company/:name

### Phase 1d — Neo4j Graph
- Entity co-occurrence → graph write pipeline
- Canonical entity resolution ("Microsoft" vs "Microsoft Corp" vs "MSFT")
- Not started

---

## Development Log

### 2026-07-25 — Session 1: Foundation
- Full brainstorm, system design, project docs created
- GitHub repo initialized: mavinash-dev/tech-intel

### 2026-07-25 — Session 2: Full Phase 1a + 1b Build
- Built entire ingestion pipeline (6 sources), Ollama classifier, APScheduler daemon
- Built briefing generator, Telegram delivery, HTML formatter
- Fixed: Python 3.9 type hint incompatibility, UTC/IST timezone offset, Telegram data= vs json=, hex opacity visibility bug
- 18/18 smoke tests passing

### 2026-07-25 — Session 3: UI Iteration
- Multiple rounds of HTML briefing improvements
- Added domain hashtag-style tags → then removed (too noisy)
- Added company brand colors, watch section with glow effects
- Fixed hex opacity (#color15) invisible on dark background
- Switched to HTML file delivery (sendDocument) to bypass Telegram formatting limits

### 2026-07-25 — Session 4: Company Watch + Intelligence Design
- Expanded watchlist from 12 → 157 companies across 14 global categories
- Company watch rebuilt as clickable accordion with real DB signal links
- Added predictions accordion (same <details> pattern, zero JS)
- Signal deduplication across briefings (last_shown_at column)
- Diversity selection algorithm: pool of 40, greedy company-rotation pick of 8
- Responsive UI with clamp() font sizes and mobile breakpoint
- send_now.py now runs ingestion first → fresh data every run
- Discussed company 360 RAG architecture — seed_company.py + ask.py planned

---

## Blockers
- Reddit: REDDIT_CLIENT_ID/SECRET not in .env
- Product Hunt: 403 error (their API now requires auth)
- No historical data yet (ingestion only covers since daemon started)

---

## Time Tracker

| Date | Session | Hours | Cumulative |
|---|---|---|---|
| 2026-07-25 | Brainstorm + Foundation | 1h | 1h |
| 2026-07-25 | Phase 1a + 1b full build | 4h | 5h |
| 2026-07-25 | UI iteration (Telegram format, HTML, colors) | 2h | 7h |
| 2026-07-25 | Company watch + intelligence design | 2h | 9h |

---

## Key Decisions Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-25 | Ollama-only for Phase 1 | No API key needed, fully free and local |
| 2026-07-25 | SQLite before Neo4j | Zero-config start, graph added once ingestion stable |
| 2026-07-25 | Telegram over WhatsApp | WhatsApp Business API is paid |
| 2026-07-25 | launchd for daemon | Native macOS, survives sleep/reboot |
| 2026-07-25 | HTML file via sendDocument | Bypasses Telegram 4096 char limit and HTML parse mode issues |
| 2026-07-25 | RAG over LLM memory for company facts | LLM training data is frozen/stale — retrieve from grounded sources instead |
| 2026-07-25 | HN Algolia as historical seed | Free, unlimited, goes back to 2006, searchable by company name + date range |
| 2026-07-25 | Source coverage must match company geography | US sources don't cover Zepto, DeepSeek well — need regional RSS feeds |
