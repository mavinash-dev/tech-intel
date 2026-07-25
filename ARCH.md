# Architecture Document
## tech-intel

**Version:** 0.3 — Company Intelligence + Graph (Phase 3 design)
**Created:** 2026-07-25
**Updated:** 2026-07-25

---

## 1. Tech Stack

### Current (Phase 2 — fully cloud, live)
| Layer | Technology | Status |
|---|---|---|
| Scheduler / compute | GitHub Actions (cron) | ✅ Live |
| Database | Turso (libSQL cloud) | ✅ Live |
| AI — classification | Gemini 2.0 Flash (google-genai SDK) | ✅ Live |
| AI — briefing gen | Gemini 2.0 Flash | ✅ Live |
| Notifications | Telegram Bot API | ✅ Live |
| Briefing publishing | GitHub Pages (docs/index.html) | ✅ Live |
| Mac | Nothing running | ✅ Zero dependency |

### Planned (Phase 3 — company intelligence)
| Layer | Technology | Status |
|---|---|---|
| Historical seeding | HN Algolia API + Wikipedia API + arXiv API | 🔄 Next |
| RAG query CLI | ask.py (Turso retrieval → Gemini synthesis) | 🔄 Next |
| Company HTML profiles | company_page.py → docs/companies/*.html | 🔄 Next |
| Regional news sources | YourStory, Inc42, TechNode, 36Kr RSS | 🔄 Next |

### Planned (Phase 4 — knowledge graph)
| Layer | Technology | Status |
|---|---|---|
| Graph DB | Neo4j AuraDB free tier (200MB) | Planned |
| Entity resolution | Canonical name map before graph writes | Planned |
| Graph queries | Cypher — co-occurring entities, signal chains | Planned |

---

## 2. Architecture Overview

### Live Architecture (Phase 2)
```
┌─────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS                        │
│                                                         │
│  ┌─────────────────────────────────────────┐            │
│  │  ingest.yml  (cron: every 30 min)       │            │
│  │                                         │            │
│  │  HN + RSS + GitHub + Dev.to             │            │
│  │       │                                 │            │
│  │       ▼                                 │            │
│  │  Gemini Flash — batch classify (5/prompt)│           │
│  │       │                                 │            │
│  │       ▼                                 │            │
│  │    Turso (libSQL cloud)                 │            │
│  └─────────────────────────────────────────┘            │
│                                                         │
│  ┌─────────────────────────────────────────┐            │
│  │  briefing.yml  (cron: every 1 hour)     │            │
│  │                                         │            │
│  │  load top signals from Turso            │            │
│  │       │                                 │            │
│  │       ▼                                 │            │
│  │  Gemini Flash — why it matters + question│           │
│  │       │                                 │            │
│  │       ▼                                 │            │
│  │  → Telegram (HTML file via sendDocument) │           │
│  │  → docs/index.html → GitHub Pages       │            │
│  └─────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘

Live URL: https://mavinash-dev.github.io/tech-intel/
```

### Target Architecture (Phase 3 — company intelligence added)
```
┌────────────────────────────────────────────────┐
│  seed_company.py "Nvidia"   (run once per co.) │
│                                                │
│  Wikipedia API ──► company_facts (Turso)       │
│  HN Algolia API ─► signals_raw (source=seed_hn)│
│  arXiv API ──────► signals_raw (source=seed_arxiv)
│       │                                        │
│       ▼                                        │
│  Gemini batch classify → signals_enriched      │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│  ask.py "What has Anthropic done on safety?"   │
│                                                │
│  Turso: signals_enriched WHERE mentions company│
│  Turso: company_facts WHERE company = name     │
│  Turso: predictions WHERE related_entities     │
│       │                                        │
│       ▼                                        │
│  Gemini: synthesize from context only          │
│       │                                        │
│       ▼                                        │
│  Grounded answer with [Signal #3, #7] citations│
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│  company_page.py "Nvidia"                      │
│                                                │
│  Pull facts + signals + predictions from Turso │
│  Generate HTML profile page                    │
│  → docs/companies/nvidia.html                  │
│  → pushed to GitHub Pages                      │
└────────────────────────────────────────────────┘
```

### Target Architecture (Phase 4 — knowledge graph added)
```
signals_enriched.entities_json
       │
       ▼
  entity resolver (canonicalize names)
       │
       ▼
  Neo4j AuraDB
  ┌─────────────────────────────────────┐
  │  (Company)──[SIGNAL]──(Person)      │
  │      │         │          │         │
  │  (Country)  domain,    (Technology) │
  │             date,                   │
  │             relevance               │
  └─────────────────────────────────────┘
       │
       ▼
  Cypher queries:
  "Show all entities co-occurring with Nvidia in last 90 days"
  "Which companies appear most in Power domain signals?"
  "Trace: TSMC → chip shortage → which companies are affected?"
```

---

## 3. Data Model

### Turso (libSQL) — live tables

#### signals_raw
```sql
CREATE TABLE IF NOT EXISTS signals_raw (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source       TEXT NOT NULL,   -- hn / rss / github / devto / seed_hn / seed_arxiv
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
    domain            TEXT NOT NULL,   -- Capital/Talent/Technology/Power/Infrastructure/Narrative/Security
    relevance_score   REAL NOT NULL,
    plain_explanation TEXT NOT NULL,
    entities_json     TEXT NOT NULL,   -- [{"name": "Nvidia", "type": "Company"}, ...]
    prediction        TEXT,
    enriched_at       DATETIME DEFAULT (datetime('now')),
    last_shown_at     DATETIME         -- 7-day exclusion window
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

#### company_facts (Phase 3)
```sql
CREATE TABLE IF NOT EXISTS company_facts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    company   TEXT NOT NULL,
    fact_type TEXT NOT NULL,   -- founding/ceo/hq/employees/market_cap/product/acquisition/description
    value     TEXT NOT NULL,
    source    TEXT,            -- wikipedia / wikidata / manual
    as_of     DATE,
    seeded_at DATETIME DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_facts_company ON company_facts(company);
```

### Neo4j AuraDB (Phase 4)
```
Nodes:
  (:Company {name, canonical_name, category})
  (:Person {name, role})
  (:Technology {name, type})
  (:Country {name, region})
  (:Organization {name, type})

Relationships:
  (entity1)-[:SIGNAL {
    signal_id, domain, date, relevance_score,
    summary, source_url, prediction
  }]->(entity2)
```

---

## 4. Gemini Flash — API Budget

### Classification (batch 5 signals/prompt)
```
Daily budget (1,500 req/day free tier):
  Classification:     30 signals ÷ 5 per batch = 6 calls × 48 runs = 288 calls
  Why it matters:      8 calls × 24 briefings                       = 192 calls
  Question gen:        1 call  × 24 briefings                       =  24 calls
  Pred resolution:     1 call  × 24 briefings                       =  24 calls
  ─────────────────────────────────────────────────────────────────────────────
  Live pipeline total:                                               = 528 calls/day
  ask.py queries (on demand):                                        = ~5 calls/query
  seed_company.py (one-time per company):          ~400 signals ÷ 5 = ~80 calls/seed
  ─────────────────────────────────────────────────────────────────────────────
  Headroom:                                          972 calls/day remaining
```

### Batch classification prompt structure
```
Classify these 5 signals. Return a JSON array with one object per signal, in order.

Signal 1: <title> — <body[:400]>
Signal 2: ...
...

Each object must have:
  domain: Capital|Talent|Technology|Power|Infrastructure|Narrative|Security
  relevance_score: float 0-1
  plain_explanation: 2-4 sentences plain language
  entities: [{name, type}] array
  prediction: one falsifiable forward-looking sentence, or null
```

---

## 5. Company Intelligence — seed_company.py Design

### Flow
```
python3 seed_company.py "Nvidia"

Step 1 — Wikipedia facts
  GET https://en.wikipedia.org/api/rest_v1/page/summary/Nvidia
  GET https://en.wikipedia.org/w/api.php?action=query&prop=revisions... (infobox)
  Extract: founded, hq, ceo, employees, products, subsidiaries, acquisitions
  → INSERT INTO company_facts (company, fact_type, value, source="wikipedia", as_of)

Step 2 — HN Algolia historical search
  GET https://hn.algolia.com/api/v1/search_by_date
      ?query=Nvidia&tags=story&numericFilters=created_at_i>1420070400
      Paginate with page=0,1,2... until no results
  → INSERT OR IGNORE INTO signals_raw (source="seed_hn", source_id=hn_id, ...)
  → Batch classify via Gemini (5/prompt, same classifier)
  → INSERT INTO signals_enriched

Step 3 — arXiv search (for tech/AI/semiconductor companies)
  GET http://export.arxiv.org/api/query
      ?search_query=all:Nvidia&start=0&max_results=200
  → INSERT OR IGNORE INTO signals_raw (source="seed_arxiv", ...)
  → Batch classify + store

Output:
  "Nvidia: 47 facts stored, 1,847 historical signals seeded (2015–2026)"
```

### Coverage by company type
| Company type | HN coverage | arXiv coverage | Notes |
|---|---|---|---|
| US Big Tech (Apple, Google, Meta) | Excellent (1000+) | Good | Best cold-start results |
| US AI (OpenAI, Anthropic, xAI) | Very good (500+) | Excellent | AI community heavily on HN |
| Semiconductors (TSMC, ASML, AMD) | Good (200–500) | Excellent | Technical + papers |
| Chinese tech (DeepSeek, ByteDance) | Sparse before 2023 | Limited | Need TechNode/36Kr RSS |
| Indian tech (Zepto, CRED, PhonePe) | Very sparse | None | Need YourStory/Inc42 RSS |
| European (ASML, Spotify, Revolut) | Mixed | Good for ASML | |

---

## 6. Company Intelligence — ask.py Design (RAG)

**Rule:** LLMs synthesize. They never supply facts from memory. All facts come from Turso.

```
python3 ask.py "What has Anthropic been doing with safety research?"

1. Parse: company = "Anthropic", question = full text

2. Retrieve from Turso:
   - signals_enriched WHERE entities_json LIKE '%Anthropic%'
     ORDER BY enriched_at DESC LIMIT 25
   - company_facts WHERE company = 'Anthropic'
   - predictions WHERE related_entities LIKE '%Anthropic%'

3. Format numbered context:
   [Signal 1 — 2026-07-20 — Technology]
   Title: Anthropic releases Claude 4...
   Explanation: ...
   Prediction: ...

   [Fact: CEO] Dario Amodei (as of 2026)
   [Fact: Founded] 2021, San Francisco

4. Gemini prompt:
   "Based ONLY on the following signals and facts, answer: {question}
    Cite signal numbers. Do not use outside knowledge."

5. Print grounded answer with citations
```

---

## 7. Knowledge Graph Design (Phase 4)

### Why graph on top of relational?
Turso answers "what signals mention Nvidia?" — fast and simple.
Neo4j answers "which entities consistently co-occur with Nvidia, and through which domains, over the last 6 months?" — that requires traversal across entity relationships, not just text search.

### Entity extraction pipeline (Phase 4 addition)
```
signals_enriched.entities_json → canonicalize() → Neo4j write

For each signal:
  entities = parse entities_json  → ["Nvidia", "TSMC", "Jensen Huang"]
  canonical = [CANONICAL.get(e.lower(), e) for e in entities]
  For each pair (e1, e2) in combinations(canonical, 2):
    MERGE (n1:Entity {name: e1})
    MERGE (n2:Entity {name: e2})
    CREATE (n1)-[:SIGNAL {domain, date, signal_id, relevance_score}]->(n2)
```

### Canonical entity resolution (needed before graph write)
```python
CANONICAL = {
    "microsoft corp": "Microsoft",
    "microsoft corporation": "Microsoft",
    "msft": "Microsoft",
    "open ai": "OpenAI",
    "openai llc": "OpenAI",
    "alphabet": "Google",
    "alphabet inc": "Google",
    "meta platforms": "Meta",
    "facebook": "Meta",
    # ... applied at entities_json write time
}
```

### Graph queries (Cypher examples)
```cypher
// What's co-occurring with Nvidia in the last 90 days?
MATCH (nvidia:Entity {name: "Nvidia"})-[s:SIGNAL]-(other)
WHERE s.date > date() - duration({days: 90})
RETURN other.name, s.domain, count(s) as signal_count
ORDER BY signal_count DESC

// Trace a supply chain: TSMC → who is affected?
MATCH path = (tsmc:Entity {name: "TSMC"})-[:SIGNAL*1..3]-(downstream)
WHERE ALL(r IN relationships(path) WHERE r.domain IN ['Infrastructure', 'Capital'])
RETURN downstream.name, length(path) as hops
```

---

## 8. GitHub Actions Workflows

### ingest.yml (every 30 min)
```yaml
on:
  schedule: [{cron: '*/30 * * * *'}]
  workflow_dispatch:
jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - checkout + setup-python@3.11 + pip install
      - python ingest_job.py
    env: GEMINI_API_KEY, TURSO_DATABASE_URL, TURSO_AUTH_TOKEN
```

### briefing.yml (every 1 hour)
```yaml
on:
  schedule: [{cron: '0 * * * *'}]
  workflow_dispatch:
permissions:
  contents: write   # needed to push docs/index.html to GitHub Pages
jobs:
  briefing:
    runs-on: ubuntu-latest
    steps:
      - checkout + setup-python@3.11 + pip install
      - python briefing_job.py   # generates HTML, copies to docs/index.html
      - git commit docs/index.html + git push
    env: GEMINI_API_KEY, TURSO_DATABASE_URL, TURSO_AUTH_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

---

## 9. Source Coverage

### Live (GitHub Actions, every 30 min)
| Source | Method | Status |
|---|---|---|
| Hacker News Firebase API | REST | ✅ Working |
| Reddit | PRAW OAuth | ⚠️ Needs creds in GitHub Secrets |
| RSS (TechCrunch, MIT Tech Review, arXiv, TLDR, Crunchbase, YC Blog, 7 feeds) | feedparser | ✅ Working |
| GitHub Trending | BeautifulSoup scrape | ✅ Working |
| Dev.to API | REST (no key) | ✅ Working |
| Product Hunt | GraphQL | ❌ 403 — needs replacement |

### Historical Seeding (seed_company.py, run once per company)
| Source | Purpose | Notes |
|---|---|---|
| HN Algolia API | All HN discussions mentioning company (2006→now) | Free, no key, paginated |
| Wikipedia REST API | Company summary + infobox | Free |
| arXiv API | Research papers mentioning company | Free, max 200/query |

### Planned Regional RSS (3-line additions in ingestion/rss.py)
| Region | Feed | Companies unlocked |
|---|---|---|
| India | YourStory, Inc42 | Zepto, CRED, PhonePe, Razorpay |
| China | TechNode, 36Kr English | DeepSeek, BYD, CATL, Meituan |
| SE Asia | Tech in Asia | Grab, GoTo, Sea Group |

---

## 10. Open Technical Questions

- [ ] seed_company.py: classify historical signals (Gemini cost) or store raw only and classify on-demand?
- [ ] ask.py: keyword search (free, current) or vector embeddings (better recall, needs embedding API)?
- [ ] company_page.py: generate on-demand per CLI call, or auto-generate for all 157 companies on a schedule?
- [ ] Neo4j AuraDB free tier is 200MB — how many entities before we hit the limit? (estimate: ~5000 entities × relationships ≈ enough for 2-3 years)
- [ ] Canonical entity resolution: build manually or use Gemini to normalize entity names at extraction time?
- [ ] Product Hunt replacement: Lobste.rs API, BetaList RSS, or IndieHackers RSS?
- [ ] company_facts: seed all 157 watchlist companies at once or on-demand when asked?
