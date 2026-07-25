# tech-intel

> A fully cloud-hosted signal intelligence system that ingests global tech signals, classifies them with AI, and delivers analyst-grade briefings via Telegram and a public URL. Nothing runs on Mac.

---

## Live Briefing

**[mavinash-dev.github.io/tech-intel/](https://mavinash-dev.github.io/tech-intel/)**

Auto-updated every hour via GitHub Actions. No login, no download — just open the link.

---

## What It Is

Tech Intel is a personal signal intelligence system that tracks the global technology ecosystem across 157 companies and 7 signal domains. It ingests from free public APIs every 30 minutes, classifies signals using Gemini Flash, stores everything in a cloud database, and delivers a structured briefing to Telegram + a GitHub Pages URL every hour.

Signals are classified into domains — **Capital** (investment, M&A), **Talent** (hiring, layoffs, founders), **Technology** (launches, research), **Power** (regulation, geopolitics), **Infrastructure**, **Narrative**, **Security** — with an explanation, strategic question, and prediction for each.

---

## Status

**Phase:** Phase 3 — Company Intelligence (active)  
**Phase 2:** Complete — full cloud pipeline live since 2026-07

---

## Architecture

```
GitHub Actions (every 30 min)
  → ingest_job.py
      → 5 sources: HN, RSS (7 feeds), GitHub Trending, Dev.to
      → Gemini 2.0 Flash classifier (batch 5 signals/prompt)
      → Turso (libSQL cloud) — signals_raw + signals_enriched

GitHub Actions (every 1 hour)
  → briefing_job.py
      → load signals from Turso
      → Gemini: why / question / prediction per signal
      → HTML briefing → docs/index.html (GitHub Pages)
      → Telegram sendDocument → phone
```

No server. No Mac process. No paid API.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Scheduler | GitHub Actions cron (free, unlimited for public repos) |
| AI | Gemini 2.0 Flash (`google-genai` SDK) |
| Database | Turso (libSQL cloud) — HTTP API, SQLite dialect |
| Ingestion | feedparser, requests, beautifulsoup4 |
| Notifications | Telegram Bot API (sendDocument) |
| Publishing | GitHub Pages from `docs/` on main branch |
| Language | Python 3.11 |

---

## Phase 3 — Company Intelligence (In Progress)

Per-company deep intelligence on any of the 157 watched companies:

```bash
# Cold-start a company (run once per company)
python3 seed_company.py "Nvidia"
# → Wikipedia facts → company_facts table
# → HN Algolia 2015→now → historical signals
# → arXiv papers → research signal layer

# Query grounded answers from DB (not from LLM memory)
python3 ask.py "What signals do we have about TSMC capacity constraints?"
# → retrieve 25 signals + facts → Gemini synthesis → cited answer
```

Full protocol: [docs/company-intelligence.md](docs/company-intelligence.md)

---

## Project Docs

| Document | Purpose |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Full project brief — read this first in any AI session |
| [ARCH.md](ARCH.md) | Technical architecture, data model, graph design |
| [STATUS.md](STATUS.md) | Current phase, task list, decisions log |
| [docs/company-intelligence.md](docs/company-intelligence.md) | Per-company RAG protocol |
