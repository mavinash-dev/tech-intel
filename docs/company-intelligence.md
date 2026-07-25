# Company Intelligence Protocol
## tech-intel

> How we build, store, and query 360° intelligence on any company in the watchlist.

---

## The Core Problem

Asking an LLM "tell me everything about Nvidia" is unreliable:
- Training data has a cutoff — recent events are missing
- LLMs hallucinate specifics (funding amounts, leadership changes, product timelines)
- No citations — you can't verify what it says

**The rule:** LLMs synthesize. They never supply facts from memory. All facts come from sources we control, stored in our DB, passed as context.

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
  Stored in: signals_raw → signals_enriched (same pipeline)
  When: every 30 min via GitHub Actions
```

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
      ?query={company}&dateRange=2015-01-01,{today}&hitsPerPage=200
  Paginate through all results
  → INSERT OR IGNORE INTO signals_raw (source="seed_hn", source_id=hn_id, ...)
  → Classify in batches of 5 via Gemini Flash (same classifier)
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
| Chinese tech (DeepSeek, ByteDance) | Sparse before 2023 | Limited | Need TechNode/36Kr RSS |
| Indian tech (Zepto, CRED, PhonePe) | Very sparse | None | Need YourStory/Inc42 RSS |
| European (ASML, Spotify, Revolut) | Mixed | Good for ASML | |

**Action:** for companies with weak HN coverage, add regional RSS feeds before seeding.

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
| Trends visible in our ingestion window | Events before 2015 seed |
| Prediction history + outcomes | Real-time news from last 30min |

---

## company_facts Table Schema

```sql
CREATE TABLE IF NOT EXISTS company_facts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company     TEXT NOT NULL,        -- canonical name matching COMPANY_BRAND key
    fact_type   TEXT NOT NULL,        -- see fact types below
    value       TEXT NOT NULL,        -- the fact value as plain text
    source      TEXT,                 -- wikipedia / wikidata / manual
    as_of       DATE,                 -- when this fact was true (important for CEO changes etc.)
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

## Per-Company HTML Profile (Planned)

When we have enough signals per company, generate a dedicated company page.

```bash
python3 company_page.py "Nvidia"
→ generates companies/nvidia.html
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

## Regional Source Coverage Plan

The quality of any company's intelligence is only as good as the sources covering it.

### Needed additions (planned)

| Region | RSS Sources to add | Companies it unlocks |
|---|---|---|
| India | YourStory (`yourstory.com/feed`), Inc42 (`inc42.com/feed`) | Zepto, CRED, PhonePe, Razorpay, Meesho, Zomato |
| China | TechNode (`technode.com/feed`), 36Kr English (`36kr.com/en/feed`) | DeepSeek, CATL, BYD, Meituan, SenseTime |
| Southeast Asia | Tech in Asia (`techinasia.com/feed`) | Grab, GoTo, Sea Group |
| Korea | Korea Herald Tech (`koreaherald.com/feed`) | Kakao, Naver, SK Hynix detail |
| Israel | CTech (`calcalistech.com/feed`) | Wiz, Check Point, CyberArk |

Adding each is a 3-line change in `ingestion/rss.py`.

---

## Canonical Entity Names

The same company can appear as:
- "Microsoft" / "Microsoft Corp" / "Microsoft Corporation" / "MSFT"
- "OpenAI" / "Open AI" / "OpenAI LLC"

Before writing to Neo4j (Phase 1d) and for `ask.py` retrieval to work correctly, we need a canonical name map.

### Resolution strategy (planned)

```python
CANONICAL = {
    "microsoft corp": "Microsoft",
    "microsoft corporation": "Microsoft",
    "msft": "Microsoft",
    "open ai": "OpenAI",
    "openai llc": "OpenAI",
    # ... etc
}

def canonicalize(name: str) -> str:
    return CANONICAL.get(name.lower().strip(), name)
```

Applied at entity extraction time in the classifier — before storing entities_json.

---

## Priority Order for Building

1. **seed_company.py** — unlocks history for every company, makes ask.py useful
2. **ask.py** — the query interface; needs seed data to be meaningful
3. **Regional RSS feeds** — 3-line additions, big coverage unlock for non-US companies
4. **company_page.py** — HTML profile; needs enough signals per company first
5. **Canonical entity resolution** — needed before Neo4j graph write

---

## Example: What a full Nvidia 360 looks like

After running `seed_company.py "Nvidia"`:

```
company_facts:    12 facts (founding, CEO, products, acquisitions, market cap)
signals_enriched: 1,847 historical + ongoing live signals

ask.py "Summarise Nvidia's trajectory from 2020 to now":

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
