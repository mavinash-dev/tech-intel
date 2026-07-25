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
  - source: TEXT (hackernews / reddit / rss / github / devto / seed_hn / seed_wiki)
  - source_id: TEXT (external ID for dedup — UNIQUE with source)
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
  - domain: TEXT (Capital / Talent / Technology / Power / Infrastructure / Narrative / Security)
  - relevance_score: FLOAT (0-1, assigned by Ollama)
  - plain_explanation: TEXT (Ollama-generated plain language explanation)
  - entities_json: TEXT (JSON array of extracted entity names + types)
  - prediction: TEXT (forward-looking statement generated per signal)
  - enriched_at: DATETIME
  - last_shown_at: DATETIME (NULL until first briefing — used to rotate signals, exclude recently shown)
```

### SQLite — Predictions Table
```
predictions
  - id: INTEGER PRIMARY KEY
  - made_at: DATETIME
  - briefing_date: DATE
  - prediction_text: TEXT
  - related_entities: TEXT (comma-separated entity names)
  - domain: TEXT
  - status: TEXT DEFAULT 'watching' (watching / confirmed / wrong / expired)
  - resolved_at: DATETIME
  - resolution_note: TEXT (Ollama-written on resolution)
  - signal_id: INTEGER → signals_enriched.id
```

### Planned: company_facts Table (Phase 2 — Company 360)
```
company_facts
  - id: INTEGER PRIMARY KEY
  - company: TEXT (canonical name, matches COMPANY_BRAND key)
  - fact_type: TEXT (founding / ceo / hq / product / acquisition / funding / headcount)
  - value: TEXT
  - source: TEXT (wikipedia / wikidata / crunchbase_rss)
  - as_of: DATE (when this fact was true)
  - seeded_at: DATETIME
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

### Live Ingestion (current)
| Source | Method | Rate Limits | Status |
|---|---|---|---|
| Hacker News Firebase API | REST | None | ✅ Working |
| Reddit | PRAW OAuth | 60 req/min | ⚠️ Needs creds in .env |
| RSS feeds (TechCrunch, MIT Tech Review, arXiv, TLDR, Crunchbase, YC Blog) | feedparser | None | ✅ Working |
| GitHub Trending | BeautifulSoup scrape | Informal | ✅ Working |
| Dev.to API | REST (no key) | 1000 req/day | ✅ Working |
| Product Hunt GraphQL | GraphQL | N/A | ❌ 403 — needs auth now |
| Telegram Bot API | REST | None personal | ✅ Working |
| Ollama (local) | Local HTTP | No limits | ✅ Working |

### Historical Seeding (planned — seed_company.py)
| Source | Purpose | Range | Notes |
|---|---|---|---|
| HN Algolia API | Historical HN discussions per company | 2006 → now | Free, no key, searchable by date + query |
| Wikipedia API | Structured company facts (founding, CEO, products, acquisitions) | As of seed date | Free, returns infobox JSON |
| Wikidata API | Machine-readable facts with timestamps | As of seed date | Free, structured, linked data |
| arXiv API | Research papers mentioning a company | 2010 → now | Free, date-range search |

### Planned Regional RSS (for non-US companies)
| Region | Source | Companies covered |
|---|---|---|
| India | YourStory RSS, Inc42 RSS | Zepto, CRED, PhonePe, Razorpay, Meesho |
| China | TechNode RSS, 36Kr English | DeepSeek, BYD, CATL, Meituan |
| Southeast Asia | Tech in Asia RSS | Grab, GoTo, Sea Group |

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

## 6. Company 360 Intelligence Architecture (Planned)

### Problem
Asking Ollama "tell me about Nvidia" returns stale, potentially hallucinated facts from training data. We need grounded, sourced, time-stamped facts.

### RAG Design (Retrieval-Augmented Generation)
LLM role = synthesis only. All facts come from sources we control.

```
Query: "What has Anthropic been doing with safety research?"
         │
         ▼
  Retrieve from DB
  ┌─────────────────────────────────────┐
  │ signals_raw WHERE title LIKE '%Anthropic%'
  │ signals_enriched (entities_json)
  │ company_facts WHERE company = 'Anthropic'
  │ predictions WHERE related_entities LIKE '%Anthropic%'
  └─────────────────────────────────────┘
         │
         ▼ (formatted as context)
     Ollama
  "Based on these signals: [context]
   Answer: [cited, grounded response]"
```

### Cold Start Per Company (seed_company.py)
```
python3 seed_company.py "Nvidia"

1. Wikipedia API → get infobox (founding, CEO, HQ, products, market cap)
   → store in company_facts table

2. HN Algolia API → search "nvidia" from 2015-01-01 to today
   → paginate through results (~500-2000 items)
   → feed into signals_raw with source="seed_hn"
   → classify with Ollama batch (same pipeline)

3. arXiv API → search papers mentioning "nvidia" (for chip/AI companies)
   → store abstracts as signals

Result: 10 years of signal in ~3 minutes. Company watch card goes from
"No signals" to 500+ searchable, classified items.
```

### Coverage Depends on Company Geography
- Apple / Google / OpenAI → HN has thousands of items, excellent coverage
- Zepto / CRED (India) → HN has almost nothing, need YourStory/Inc42 RSS
- DeepSeek / ByteDance → sparse English coverage until 2024, need TechNode
- TSMC / ASML → good arXiv/tech press coverage, limited HN community discussion

### ask.py (RAG Query Interface)
```
python3 ask.py "What signals do we have about TSMC's capacity expansion?"

→ Retrieve top 20 relevant signals from DB (keyword + entity match)
→ Format as numbered context block
→ Ollama: synthesize with citations [Signal #3, #7, #12]
→ Print grounded answer
```

---

## 7. Key Technical Decisions

### Decision 1: SQLite before Neo4j
- **Chose:** SQLite for raw and enriched signal store, Neo4j only for processed graph
- **Because:** Zero-config, immediate start, easy SQL debugging. Neo4j added in Phase 1d.

### Decision 2: Ollama over Claude API (Phase 1)
- **Chose:** Ollama with Llama 3.2 for all AI tasks
- **Because:** Fully free, no rate limits, local. Claude API slot reserved for Phase 3 synthesis quality upgrade.

### Decision 3: Telegram sendDocument over sendMessage
- **Chose:** Send HTML file as document, plus short text summary
- **Because:** Telegram's sendMessage has 4096 char limit and HTML parse mode restrictions. sendDocument has no size limit, renders in browser on tap.

### Decision 4: RAG over LLM memory for company facts
- **Chose:** Retrieve from grounded DB, pass as context to Ollama
- **Because:** LLM training data is frozen and hallucination-prone on company specifics. Grounded retrieval gives cited, verifiable answers.

### Decision 5: HN Algolia as historical seed
- **Chose:** HN Algolia API (search.hnn.algolia.com) for back-window
- **Because:** Free, unlimited, covers 2006→now, searchable by query + date range. Best available free source for English-language tech history.

### Decision 6: last_shown_at for signal rotation
- **Chose:** Track last briefing appearance per signal, exclude for 12h
- **Because:** Without this, the 2-3 highest-scored signals dominate every briefing. Rotation ensures each run surfaces fresh content.

---

## 8. Infrastructure & Deployment

- **Environments:** Local only (Mac Air)
- **CI/CD:** None — manual git push to GitHub for backup
- **Domain:** localhost:3000 (web UI, Phase 1c), localhost:8000 (API, Phase 1c)
- **Secrets:** `.env` gitignored — Telegram token, Reddit creds
- **Persistence:** launchd plist in `~/Library/LaunchAgents/` (planned)

---

## 9. Open Technical Questions

- [ ] Does Llama 3.2 3B give sufficient entity extraction quality, or do we need 7B?
- [ ] Should seed_company.py classify all historical signals (slow) or just store raw (fast)?
- [ ] For ask.py — keyword search or vector similarity? sqlite-vec adds embedding search locally.
- [ ] How to canonicalize "Microsoft" vs "Microsoft Corp" vs "MSFT" before Neo4j write?
- [ ] Should company_facts be seeded for all 157 watchlist companies at once or on-demand?
