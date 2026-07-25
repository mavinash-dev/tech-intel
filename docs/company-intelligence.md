# Company Intelligence Protocol
## tech-intel

> How we build, store, and query 360° intelligence on any company in the watchlist — and how that connects to the knowledge graph.

---

## The Core Problem

Asking an LLM "tell me everything about Nvidia" is unreliable:
- Training data has a cutoff — recent events are missing
- LLMs hallucinate specifics (funding amounts, leadership changes, product timelines)
- No citations — you can't verify what it says

**The rule:** LLMs synthesize. They never supply facts from memory. All facts come from sources we control, stored in Turso, passed as context.

---

## Three Data Layers Per Company

```
Layer 1 — Structured facts (one-time seed, refreshed periodically)
  Source: Wikipedia API + Wikidata API
  What: founding year, HQ, CEO, key products, major acquisitions,
        employee count, market cap history, parent/subsidiary relationships
  Stored in: company_facts table
  When: run seed_company.py once per company

Layer 2 — Historical signals (back-window seed, one-time per company)
  Source: HN Algolia API (2015 → now, free, unlimited)
           arXiv API (research papers mentioning the company)
  What: community discussion, technical analysis, funding news,
        controversies, product launches as they happened
  Stored in: signals_raw (source="seed_hn" / "seed_arxiv") → classified → signals_enriched
  When: run seed_company.py once per company (~500–2000 HN items per major company)

Layer 3 — Live signals (ongoing, automated)
  Source: existing ingestion pipeline (HN, RSS, GitHub, Dev.to)
  What: real-time news and discussion as it happens
  Stored in: signals_raw → signals_enriched (same pipeline, same schema)
  When: every 30 min via GitHub Actions ingest.yml
```

**Layers 2 and 3 share the same schema** — seed_hn signals and live signals are both in `signals_raw` + `signals_enriched`. The only difference is the `source` field (`seed_hn` vs `hn`). `ask.py` queries both seamlessly.

---

## seed_company.py — Cold Start Protocol

Run once per company to populate Layers 1 and 2.

```bash
python3 seed_company.py "Nvidia"
python3 seed_company.py "Zepto"
python3 seed_company.py "TSMC"
```

### What it does

```
Step 1 — Wikipedia structured facts
  GET https://en.wikipedia.org/api/rest_v1/page/summary/{company}
  GET https://en.wikipedia.org/w/api.php?action=query&prop=revisions... (infobox)
  Extract: founded, headquarters, CEO, number of employees, key products,
           parent company, subsidiaries, notable acquisitions
  → INSERT INTO company_facts (company, fact_type, value, source, as_of)

Step 2 — HN Algolia historical search
  GET https://hn.algolia.com/api/v1/search_by_date
      ?query={company}&tags=story&numericFilters=created_at_i>1420070400
  Paginate through all results (page=0, 1, 2... until empty)
  → INSERT OR IGNORE INTO signals_raw (source="seed_hn", source_id=hn_id, ...)
  → Classify in batches of 5 via Gemini Flash (same classifier as live pipeline)
  → INSERT INTO signals_enriched

Step 3 — arXiv search (for tech/AI/semiconductor companies)
  GET http://export.arxiv.org/api/query
      ?search_query=all:{company}&start=0&max_results=200
  → INSERT OR IGNORE INTO signals_raw (source="seed_arxiv", ...)
  → Classify and store

Output:
  "Nvidia: 47 facts stored, 1,847 historical signals seeded (2015–2026)"
```

### Coverage by company type

| Company type | HN coverage | arXiv coverage | Notes |
|---|---|---|---|
| US Big Tech (Apple, Google, Meta) | Excellent (1000+ items) | Good | Best cold-start results |
| US AI (OpenAI, Anthropic, xAI) | Very good (500+ items) | Excellent | AI community heavily on HN |
| Semiconductors (TSMC, ASML, AMD) | Good (200–500 items) | Excellent | Technical discussion + papers |
| Chinese tech (DeepSeek, ByteDance) | Sparse before 2023 | Limited | Need TechNode/36Kr RSS first |
| Indian tech (Zepto, CRED, PhonePe) | Very sparse | None | Need YourStory/Inc42 RSS first |
| European (ASML, Spotify, Revolut) | Mixed | Good for ASML | |

**Action:** for companies with weak HN coverage, add regional RSS feeds before seeding so live Layer 3 fills the gap.

---

## ask.py — RAG Query Interface

Ask any question about a company. Answers are grounded in signals from the DB, not LLM memory.

```bash
python3 ask.py "What has Anthropic been doing with safety research?"
python3 ask.py "What signals do we have about TSMC capacity constraints?"
python3 ask.py "Summarise Nvidia's last 6 months across all domains"
python3 ask.py "What predictions did we make about OpenAI and were they right?"
```

### How it works

```
1. Parse company name + question from input

2. Retrieve from Turso:
   - signals_enriched WHERE entities_json LIKE '%{company}%'
     ORDER BY enriched_at DESC LIMIT 25
   - company_facts WHERE company = '{company}'
   - predictions WHERE related_entities LIKE '%{company}%'

3. Format as numbered context block:
   [Signal 1 — 2026-07-20 — Technology]
   Title: Nvidia announces Blackwell B200 GPU...
   Explanation: ...
   Prediction: ...

   [Fact: CEO] Jensen Huang (as of 2026)
   [Fact: Founded] 1993, Santa Clara CA
   ...

4. Send to Gemini Flash:
   "Based only on the following signals and facts, answer: {question}
    Cite signal numbers when making claims. Do not use outside knowledge."

5. Print grounded answer with citations
```

### What you get vs. what you don't

| ✅ You get | ❌ You don't get |
|---|---|
| Answers grounded in real signals | Anything not in our DB |
| Citations: "Signal #3, #7 support this" | Hallucinated company facts |
| Trends visible across our full history | Events before 2015 seed |
| Prediction history + outcomes | Real-time news from last 30 min |
| Both seed (historical) + live signals | Context from other companies unless overlapping |

---

## company_facts Table Schema

```sql
CREATE TABLE IF NOT EXISTS company_facts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company     TEXT NOT NULL,        -- canonical name matching COMPANY_BRAND key
    fact_type   TEXT NOT NULL,        -- see fact types below
    value       TEXT NOT NULL,        -- the fact value as plain text
    source      TEXT,                 -- wikipedia / wikidata / manual
    as_of       DATE,                 -- when this fact was true (CEO changes etc.)
    seeded_at   DATETIME DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_facts_company ON company_facts(company);
```

### Fact types
```
founding        — "1993"
hq              — "Santa Clara, California, USA"
ceo             — "Jensen Huang"
employees       — "29,600 (2024)"
market_cap      — "$3.3 trillion (July 2026)"
product         — "H100 GPU, Blackwell B200, CUDA platform"
acquisition     — "Mellanox Technologies ($6.9B, 2020)"
parent          — null / "Alphabet Inc" (for subsidiaries)
subsidiary      — "Arm Holdings (partial stake)"
description     — one-paragraph company description
founded_by      — "Jensen Huang, Curtis Priem, Chris Malachowsky"
ipo             — "1999, NASDAQ: NVDA"
```

---

## Per-Company HTML Profile — company_page.py (Planned)

```bash
python3 company_page.py "Nvidia"
→ generates docs/companies/nvidia.html
→ published to GitHub Pages: mavinash-dev.github.io/tech-intel/companies/nvidia.html
```

### Page sections
1. **Facts** — founding, CEO, products, key acquisitions (from company_facts)
2. **Signal Timeline** — all signals sorted by date, filterable by domain
3. **Domain Breakdown** — how many signals per domain (Capital vs Technology vs Power)
4. **Co-occurring Entities** — who/what appears alongside this company most often
5. **Prediction History** — all predictions made about this company + outcomes
6. **Strategic Question** — Gemini-generated synthesis: "What's the key thing to watch?"

The company watch accordion in the briefing will link to this page when it exists.

---

## Knowledge Graph — How Company Intelligence Feeds Phase 4

The same signals and entities used by `ask.py` are the raw material for the Neo4j knowledge graph.

```
signals_enriched.entities_json
  [{"name": "Nvidia", "type": "Company"},
   {"name": "TSMC", "type": "Company"},
   {"name": "Jensen Huang", "type": "Person"}]
          │
          ▼
  canonicalize() — normalize name variants
          │
          ▼
  Neo4j AuraDB write:
    MERGE (nvidia:Company {name: "Nvidia"})
    MERGE (tsmc:Company {name: "TSMC"})
    CREATE (nvidia)-[:SIGNAL {domain: "Infrastructure", date: ..., signal_id: ...}]->(tsmc)
```

### What the graph unlocks that Turso can't do

| Question | Turso (text search) | Neo4j (graph traversal) |
|---|---|---|
| "What signals mention Nvidia?" | ✅ Fast LIKE query | ✅ Node lookup |
| "Who co-occurs with Nvidia most?" | ⚠️ Need to parse entities_json per row | ✅ Single MATCH query |
| "Which companies are downstream of TSMC?" | ❌ Can't traverse relationships | ✅ Variable-depth MATCH |
| "How does a US export ban reach Chinese AI labs?" | ❌ Requires manual analysis | ✅ Path query |
| "Which entities appear in both Power + Capital signals?" | ⚠️ Multi-query + Python join | ✅ MATCH with WHERE clause |

**The graph is a lens on the same data, not a replacement.** Turso stays the source of truth. Neo4j is an index for relationship queries.

---

## Regional Source Coverage Plan

The quality of any company's intelligence is only as good as the sources covering it.

### Needed additions (planned — 3-line change each in ingestion/rss.py)

| Region | RSS Sources | Companies unlocked |
|---|---|---|
| India | YourStory (`yourstory.com/feed`), Inc42 (`inc42.com/feed`) | Zepto, CRED, PhonePe, Razorpay, Meesho, Zomato |
| China | TechNode (`technode.com/feed`), 36Kr English (`36kr.com/en/feed`) | DeepSeek, CATL, BYD, Meituan, SenseTime |
| Southeast Asia | Tech in Asia (`techinasia.com/feed`) | Grab, GoTo, Sea Group |
| Korea | Korea Herald Tech | Kakao, Naver, SK Hynix detail |
| Israel | CTech (`calcalistech.com/feed`) | Wiz, Check Point, CyberArk |

---

## Canonical Entity Names

The same company can appear as:
- "Microsoft" / "Microsoft Corp" / "Microsoft Corporation" / "MSFT"
- "OpenAI" / "Open AI" / "OpenAI LLC"

This matters for both `ask.py` (LIKE search misses variants) and Neo4j (creates duplicate nodes).

### Resolution strategy (planned — applied at entities_json write time)

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
    # ...
}

def canonicalize(name: str) -> str:
    return CANONICAL.get(name.lower().strip(), name)
```

Applied in `classifier/gemini_classifier.py` before writing `entities_json` — fixes both ask.py retrieval and Neo4j deduplication in one place.

---

## Priority Order for Building

1. **seed_company.py** — unlocks history for every company, makes ask.py immediately useful
2. **ask.py** — the query interface; needs seed data to be meaningful
3. **Regional RSS feeds** — 3-line additions, big coverage unlock for non-US companies
4. **company_page.py** — HTML profile; needs enough signals per company first
5. **Canonical entity resolution** — needed before Neo4j graph write
6. **Neo4j AuraDB (Phase 4)** — relationship queries on top of the same entity data

---

## Example: Full Nvidia 360 After Seeding

```
company_facts:    12 facts (founding, CEO, products, acquisitions, market cap)
signals_enriched: 1,847 historical (seed_hn) + ongoing live signals

python3 ask.py "Summarise Nvidia's trajectory from 2020 to now"

  Based on 23 retrieved signals:

  [Capital domain — Signals #1, #4, #8]
  Nvidia's market cap grew from ~$300B (2020) to $3.3T (2026), driven by
  data center GPU demand. The Mellanox acquisition ($6.9B, Signal #1) gave
  them InfiniBand networking dominance in HPC clusters.

  [Technology domain — Signals #2, #6, #11, #15]
  Three GPU generations in this window: Ampere (2020), Hopper H100 (2022),
  Blackwell B200 (2024). CUDA platform lock-in is the consistent moat
  mentioned across Signal #6, #11, #15.

  [Power domain — Signals #3, #9]
  US export controls on H100/A100 to China (Signal #3, 2022) forced Nvidia
  to create China-specific chips (H20) with reduced specs (Signal #9, 2023).

  Key watch: AMD MI300X and custom silicon from Google (TPU), Amazon (Trainium),
  Microsoft (Maia) are the competitive signals worth tracking — see Signal #17, #21.
```

That's the target. Grounded, cited, domain-structured, historically aware.
