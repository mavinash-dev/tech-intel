# tech-intel — Project Brief for Claude

> Read this first. Every session. This is your full context.

---

## What This Project Is

**One-liner:** A local signal intelligence system that ingests global tech signals, builds a connected knowledge graph, and delivers analyst-grade plain-language briefings via Telegram and a local web app.

**Problem:** Most tech news is surface-level and developer-centric. The deeper signals — capital flows, talent movements, regulatory shifts, infrastructure control — require cross-domain pattern recognition across time and geography that no existing free tool provides. Avinash has 4 years in the industry but has never followed tech news and is building his understanding from scratch.

**Solution:** A fully cloud-hosted signal intelligence pipeline (GitHub Actions + Gemini Flash + Turso) that ingests from free public APIs, classifies signals with AI, and delivers rich HTML briefings via Telegram. Nothing runs on Mac — Avinash only receives Telegram notifications on his phone.

**Positioning:** Not a news aggregator. A signal intelligence layer — closer to what a VC analyst or geopolitical tech strategist uses, but personal, local, free, and self-explaining. The key differentiator is the AI explanation layer: every signal is explained in plain language for someone building their understanding, not just consuming headlines.

---

## Target Users

- **Primary:** Avinash — software engineer, 4 years experience, new to following global tech ecosystem, Mac Air, everything local
- **Secondary:** 2 friends max, same local setup or shared briefing exports
- **Not targeting:** Enterprise, public users, paid subscribers, anyone outside the 3-person circle

---

## Current Phase & Status

**Phase:** Phase 2 — Cloud migration
**Status:** Active — migration in progress
**Last worked on:** 2026-07-25

**What's done (Phase 1b — complete):**
- [x] Full ingestion pipeline: HN, Reddit, RSS (7 feeds), GitHub Trending, Dev.to
- [x] Ollama + Llama3.2 classifier with domain/entities/score/explanation/prediction
- [x] SQLite schema: signals_raw, signals_enriched, predictions
- [x] Signal dedup: UNIQUE(source, source_id) + last_shown_at 7-day exclusion
- [x] Briefing generator: pool of 60, diversity-selects 8 across watchlist companies
- [x] HTML briefing: dark theme, signal cards, predictions accordion, 157-company watch accordion
- [x] Telegram delivery: text summary + HTML file as sendDocument
- [x] send_now.py: runs ingestion first then generates briefing

**What's next (Phase 2 — cloud migration):**
- [ ] Step 1: Replace Ollama with Gemini Flash (batch 5 signals/prompt)
- [ ] Step 2: Replace SQLite with Turso (libSQL-compatible, zero SQL changes)
- [ ] Step 3: GitHub Actions workflows (ingest.yml every 30min, briefing.yml every 1h)
- [ ] Step 4: Add secrets to GitHub, test end-to-end, shut down Mac daemon

---

## Core Features (Phase 1)

1. **Signal Ingestion Daemon** — Python + APScheduler, runs every 30 min, pulls from HN/Reddit/RSS/GitHub, deduplicates by source_id, stores in SQLite
2. **Ollama Classification** — Every signal classified by domain (Capital/Talent/Technology/Power/Infrastructure/Narrative), entities extracted, relevance scored 0-1, plain-language explanation generated
3. **Neo4j Knowledge Graph** — Entities as nodes (Company, Person, Technology, Country), signals as relationships with timestamps — compounding over time
4. **Daily Briefing** — 8am scheduled job synthesizes top signals → Ollama generates analyst-style plain-language briefing → sent to Telegram bot
5. **Local Web UI** — Next.js at localhost:3000: today's briefing, filterable signal feed, entity explorer, system status

---

## Tech Stack

- **Language:** Python 3.11 (backend), TypeScript (web UI — Phase 1c, not started)
- **Ingestion:** GitHub Actions cron (replacing APScheduler daemon), feedparser (RSS), PRAW (Reddit), requests (HN/GitHub)
- **AI:** Gemini 2.0 Flash API (replacing Ollama) — batch 5 signals per prompt, free 1500 req/day
- **DB:** Turso (libSQL cloud, replacing local SQLite) — same SQL dialect, free 500MB
- **Graph DB:** Neo4j AuraDB free tier (replacing Neo4j Desktop) — Phase 1d, not started
- **API:** FastAPI (localhost:8000)
- **Web UI:** Next.js App Router (localhost:3000)
- **Notifications:** Telegram Bot API (free)
- **Process mgmt:** launchd plist for Mac daemon persistence

---

## Hard Constraints

- Everything must be free — no paid APIs, no paid hosting
- Nothing should run on Mac Air — full cloud pipeline (GitHub Actions + Turso + Gemini)
- Gemini Flash free tier: 1500 req/day — batch classification keeps us well under this
- No WhatsApp (requires paid Meta Business API) — Telegram only
- No user auth, no multi-user complexity — max 3 people, same machine or local network
- All secrets in .env, gitignored — Telegram token is the only secret

---

## Key Decisions Already Made

- **SQLite before Neo4j** — Start ingestion immediately, add graph layer once stable
- **Ollama Llama 3.2** — Fully free, local, no rate limits. Claude API slot reserved for later.
- **Telegram** — Free bot API, works on phone, 5-minute setup
- **launchd** — Native macOS daemon persistence, survives sleep/reboot
- **Explain everything** — Every signal shown to user has a plain-language explanation. No raw data without context.
- **Domain taxonomy** — Capital / Talent / Technology / Power / Infrastructure / Narrative

---

## Signal Sources (Phase 1, all free)

| Source | Library/Method | Data |
|---|---|---|
| Hacker News | Firebase REST API | Top/new stories |
| Reddit | PRAW (read-only OAuth) | r/technology, r/programming, r/MachineLearning |
| TechCrunch | RSS (feedparser) | Headlines + summaries |
| MIT Tech Review | RSS (feedparser) | Headlines + summaries |
| arXiv CS | RSS (feedparser) | Research paper titles |
| TLDR Newsletter | RSS (feedparser) — tldr.tech/rss | Curated tech + AI + infosec daily |
| Crunchbase News | RSS (feedparser) | Funding rounds, acquisitions |
| Y Combinator Blog | RSS (feedparser) | Startup ecosystem signals |
| GitHub Trending | HTML scrape | Daily trending repos |
| Dev.to | REST API (no key) | Articles by tag |
| Product Hunt | REST API (no key) — public posts endpoint | New product launches, emerging tools |

---

## Data Model Summary

**SQLite:**
- `signals_raw` — source, source_id (dedup key), title, url, body, published_at, processed flag
- `signals_enriched` — domain, relevance_score, plain_explanation, entities_json, enriched_at
- `predictions` — prediction_text, domain, related_entities, status (watching/confirmed/wrong/expired), made_at, resolved_at, resolution_note, signal_id

**Neo4j:**
- Nodes: Company, Person, Technology, Country, Organization
- Relationships: SIGNAL (type, date, domain, summary, source)

---

## Project Files

- `PRD.md` — Full product requirements, features, roadmap
- `ARCH.md` — Full technical architecture, data model, API list, decisions
- `DESIGN.md` — UX flows, key screens, design principles
- `STATUS.md` — Development log, all pending tasks, time tracker
- `README.md` — Public summary and setup instructions

---

## How to Continue This Project

1. Read `STATUS.md` → Current Focus + Pending Tasks
2. Ask Avinash: "Continuing tech-intel from [last task] — ready?"
3. Work on next pending task in order (Phase 1a → 1b → 1c → 1d)
4. On session end: update `STATUS.md` Development Log + Time Tracker

---

## Important Context

- Avinash is new to following tech news — he has industry experience but zero habit of tracking ecosystem signals. The system must explain everything in plain language, not assume prior knowledge of companies, events, or terminology.
- The goal is understanding-building, not just information delivery. The daily briefing is the primary interface. The web app is secondary.
- Do NOT suggest cloud deployment, paid APIs, or user auth — explicitly out of scope.
- The Claude API slot should be mentioned as "reserved for Phase 3" when relevant, not removed from architecture.
- This project is part of Avinash's broader developer dashboard at mavinash-dev.github.io/dashboard.
