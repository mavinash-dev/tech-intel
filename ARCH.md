# Architecture Document
## tech-intel

**Version:** 0.1  
**Created:** 2026-07-25

---

## 1. Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Ingestion | Python 3.11 + APScheduler | Simple, reliable, runs as background daemon on Mac |
| Raw store | SQLite | Zero-config, local, perfect for signal queue before graph processing |
| AI classification | Ollama + Llama 3.2 | Fully local, free, no API key, runs well on Mac Air M-series |
| Knowledge graph | Neo4j Desktop (free) | Graph-native queries, local, handles entity relationships across time |
| API server | FastAPI | Lightweight Python, async, good for local query endpoint |
| Web UI | Next.js (App Router) | Matches Avinash's existing stack, fast local dev |
| Notifications | Telegram Bot API | Free, no business account needed, instant phone delivery |
| Process management | launchd (macOS) | Keeps daemon alive across sleeps and reboots |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    MAC AIR (local)                  │
│                                                     │
│  ┌──────────────┐    every 30min    ┌────────────┐  │
│  │  Free APIs   │ ──────────────→  │  Ingestion │  │
│  │  HN, Reddit  │                  │   Daemon   │  │
│  │  RSS, GitHub │                  │  (Python)  │  │
│  └──────────────┘                  └─────┬──────┘  │
│                                          │          │
│                                          ▼          │
│                                    ┌──────────┐     │
│                                    │  SQLite  │     │
│                                    │ raw store│     │
│                                    └─────┬────┘     │
│                                          │          │
│                                          ▼          │
│                                    ┌──────────┐     │
│                                    │  Ollama  │     │
│                                    │ Llama3.2 │     │
│                                    │classify +│     │
│                                    │ explain  │     │
│                                    └─────┬────┘     │
│                                          │          │
│                              ┌───────────┴──────┐   │
│                              │                  │   │
│                              ▼                  ▼   │
│                         ┌────────┐        ┌────────┐│
│                         │ Neo4j  │        │ SQLite ││
│                         │ graph  │        │enriched││
│                         └───┬────┘        └───┬────┘│
│                             │                 │     │
│                             └────────┬────────┘     │
│                                      ▼              │
│                               ┌────────────┐        │
│                               │  FastAPI   │        │
│                               │  server   │        │
│                               └─────┬──────┘        │
│                                     │               │
│                          ┌──────────┴──────────┐    │
│                          │                     │    │
│                          ▼                     ▼    │
│                    ┌──────────┐         ┌──────────┐│
│                    │ Next.js  │         │ Telegram ││
│                    │ Web UI   │         │   Bot    ││
│                    │localhost │         │  (8am)   ││
│                    │  :3000   │         └──────────┘│
│                    └──────────┘                     │
└─────────────────────────────────────────────────────┘
```

---

## 3. Data Model

### SQLite — Raw Signals Table
```
signals_raw
  - id: INTEGER PRIMARY KEY
  - source: TEXT (hackernews / reddit / rss / github)
  - source_id: TEXT (external ID for dedup)
  - title: TEXT
  - url: TEXT
  - body: TEXT (summary or first 500 chars)
  - published_at: DATETIME
  - ingested_at: DATETIME
  - processed: BOOLEAN DEFAULT FALSE
```

### SQLite — Enriched Signals Table
```
signals_enriched
  - id: INTEGER PRIMARY KEY
  - raw_id: INTEGER → signals_raw.id
  - domain: TEXT (Capital / Talent / Technology / Power / Infrastructure / Narrative)
  - relevance_score: FLOAT (0-1, assigned by Ollama)
  - plain_explanation: TEXT (Ollama-generated plain language explanation)
  - entities_json: TEXT (JSON array of extracted entity names + types)
  - enriched_at: DATETIME
```

### Neo4j — Graph Model
```
Node: Company
  - name: string (canonical)
  - aliases: [string]
  - country: string
  - sector: string

Node: Person
  - name: string
  - role: string (at time of signal)

Node: Technology
  - name: string
  - category: string (AI / Chip / Cloud / Protocol / etc.)

Node: Country
  - name: string
  - region: string

Node: Organization
  - name: string (government body, standards org, VC firm, etc.)
  - type: string

Relationship: SIGNAL
  - signal_id: integer → SQLite id
  - type: string (ACQUIRED / INVESTED_IN / HIRED / REGULATED / PARTNERED / COMPETED)
  - date: datetime
  - domain: string
  - summary: string
  - source: string
```

---

## 4. External APIs & Integrations

| API | Purpose | Rate Limits | Notes |
|---|---|---|---|
| Hacker News Firebase API | Top/new stories, item details | None (Firebase realtime) | Free, no key needed |
| Reddit API (public) | r/technology, r/programming, r/MachineLearning top posts | 60 req/min without auth | Use read-only OAuth for higher limits |
| RSS (TechCrunch, MIT Tech Review, arXiv CS) | Article headlines and summaries | None | Parse with feedparser |
| GitHub Trending (scrape) | Trending repos daily | No official API — scrape HTML | Use github-trending-api wrapper or scrape |
| Dev.to API | Articles by tag (ai, tech, programming) | 1000 req/day free | No key needed for public |
| Telegram Bot API | Send briefing to personal chat | No meaningful limit for personal use | Free, create bot via @BotFather |
| Ollama (local) | LLM inference for classification + briefing | No limits — runs locally | Must be installed on Mac separately |

---

## 5. Key Technical Decisions

### Decision 1: SQLite before Neo4j
- **Chose:** SQLite as the raw and enriched signal store, Neo4j only for the processed graph
- **Over:** Writing directly to Neo4j from ingestion
- **Because:** SQLite is zero-config and lets ingestion work immediately. Neo4j can be added in Phase 1b without touching the ingestion layer. Also enables easy debugging — SQL queries on raw signals are simpler than Cypher.

### Decision 2: Ollama over Claude API (Phase 1)
- **Chose:** Ollama with Llama 3.2 for all AI tasks
- **Over:** Claude API, OpenAI API
- **Because:** Fully free, no API key, no rate limits, runs locally. Claude API slot is built into the architecture so it can be swapped in for synthesis quality later.

### Decision 3: Telegram over WhatsApp
- **Chose:** Telegram Bot API
- **Over:** WhatsApp Business API
- **Because:** WhatsApp requires Meta Business account and costs money per message. Telegram bot is free, instant, and takes 5 minutes to set up.

### Decision 4: launchd for daemon persistence
- **Chose:** macOS launchd plist for keeping the ingestion daemon alive
- **Over:** Manual terminal process, cron, systemd
- **Because:** launchd is native to macOS, survives sleep/wake cycles, auto-restarts on crash, and doesn't require Docker or any additional tooling.

### Decision 5: Next.js for web UI [ASSUMED]
- **Chose:** Next.js App Router
- **Over:** Plain HTML, React + Vite, Svelte
- **Because:** Matches Avinash's existing stack (unified dashboard project uses Next.js). Faster to build on familiar ground.

---

## 6. Infrastructure & Deployment

- **Environments:** Local only (Mac Air)
- **CI/CD:** None (Phase 1) — manual git push to GitHub for backup
- **Domain:** localhost:3000 (web UI), localhost:8000 (API)
- **Secrets management:** `.env` file in project root, gitignored. Contains Telegram bot token. No cloud secrets needed in Phase 1.
- **Persistence across reboots:** launchd plist in `~/Library/LaunchAgents/`

---

## 7. Security Considerations

- All data stays local — no cloud storage, no third-party analytics
- `.env` file gitignored — Telegram token never committed
- Neo4j runs with local auth disabled (acceptable for personal local use)
- No user input sanitization needed — no external users, no public endpoints

---

## 8. Performance Considerations

- Ollama inference on Mac Air M-series: Llama 3.2 (3B) runs at ~20 tokens/sec — fast enough for batch classification
- SQLite handles thousands of signals easily at local scale
- Neo4j Desktop handles millions of nodes — no performance concern for months of personal use
- 30-minute ingestion interval avoids rate limit issues on free APIs

---

## 9. Open Technical Questions

- [ ] Does Llama 3.2 3B give sufficient entity extraction quality, or do we need 7B (more RAM)?
- [ ] Best Cypher query pattern for "find all signals involving Company X in the last 30 days"?
- [ ] How to handle the GitHub Trending scrape if the HTML structure changes?
- [ ] Should briefing generation happen in the daemon or as a separate scheduled script?
