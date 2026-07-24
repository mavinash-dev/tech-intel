# Product Requirements Document
## tech-intel

**Version:** 0.1  
**Author:** Avinash  
**Created:** 2026-07-25  
**Status:** Draft

---

## 1. Problem Statement

Most tech news is surface-level and developer-centric — new releases, changelogs, product launches. The deeper signals — where capital is actually flowing, what talent movements precede market shifts, which regulatory changes reshape infrastructure — are scattered across dozens of disconnected sources. No tool today connects these signals across time and geography, explains them in plain language, and builds a compounding knowledge base that gets smarter the longer it runs.

Avinash has 4 years in the industry but has never followed tech news. He wants to build genuine understanding of the global tech ecosystem — not just awareness of what launched today, but pattern recognition across capital, talent, technology, power, and infrastructure signals worldwide.

---

## 2. Vision

> A personal intelligence system that watches the global tech ecosystem for you, connects signals across companies and time, and explains what's actually shifting — delivered to your phone and browser every day.

This is not a news aggregator. It is a signal intelligence layer — closer to what a VC analyst or geopolitical tech strategist uses, but built for personal use, running locally, and explaining itself in plain language for someone building their understanding from scratch.

---

## 3. Target Users

### Primary User
- **Who:** Avinash — software engineer, 4 years in industry, new to following tech ecosystem news
- **Context:** Wants to understand global tech shifts, not just developer tooling news. Uses Mac Air, prefers everything local. Shares with 2 friends max.
- **Core pain:** No system exists that ingests global tech signals, connects them across time, and explains them plainly without assuming prior knowledge

### Secondary User
- 2 friends with similar interest — access via same local setup or shared briefing exports

### Not targeted (Phase 1)
- Enterprise teams, paid subscribers, anyone outside the 3-person circle
- Users who need real-time (sub-minute) updates
- Non-English sources

---

## 4. Goals & Success Metrics

| Goal | Metric | Target |
|---|---|---|
| Daily briefing delivered | Briefing arrives on Telegram + web every morning | 7 days streak within first 2 weeks |
| Signal coverage | Signals ingested per day | 50+ per day across 5+ source types |
| Graph growth | Entities in Neo4j | 500+ entities after 30 days |
| Understanding built | Avinash can explain a signal unprompted | Subjective — within 60 days |

### Non-Goals
- Real-time (sub-second) signal delivery
- Multi-user auth, billing, or cloud deployment
- Social features, sharing, or publishing
- Non-English signal sources (Phase 1)

---

## 5. Features — Phase 1

### Signal Ingestion Daemon
A Python background process that runs continuously on Mac, pulling from free public APIs and RSS feeds every 30 minutes. Sources: Hacker News, Reddit (r/technology, r/programming, r/MachineLearning), GitHub Trending, TechCrunch RSS, MIT Tech Review RSS, arXiv CS RSS, Dev.to API. Raw signals stored in SQLite before processing.

### Local AI Classification Layer
Every ingested signal is passed to a local Ollama model (Llama 3.2) which classifies it by domain (Capital / Talent / Technology / Power / Infrastructure / Narrative), extracts named entities (companies, people, technologies, countries), assigns a relevance score, and writes a plain-language explanation of what it means and why it might matter.

### Neo4j Knowledge Graph
Classified signals are written into a local Neo4j graph. Entities become nodes (Company, Person, Technology, Country, Organization). Signals become edges with timestamps, types, and metadata. Over time, the graph builds a connected map of who is doing what, with whom, when — enabling pattern queries across months of history.

### Daily Briefing Generator
Every morning at 8am, a scheduled job pulls the top signals from the last 24 hours, queries the graph for relevant entity connections, and passes everything to Ollama to synthesize a plain-language briefing. The briefing covers: what happened, what it means, what domain it belongs to, how it connects to things seen before, and one question worth sitting with.

### Telegram Delivery
The daily briefing is sent to a personal Telegram bot. Free, instant, works on phone. No WhatsApp (requires paid Meta Business API).

### Local Web UI
A Next.js web app running at localhost:3000 that shows: today's briefing, a scrollable signal feed with filters by domain, an entity explorer (click a company to see all signals involving it), and a simple search. No cloud hosting — localhost only.

---

## 6. Explicitly Out of Scope

- Cloud deployment or public hosting
- User authentication or multi-user accounts
- WhatsApp integration (paid API)
- Real-time (sub-minute) signal updates
- Paid data sources (Crunchbase Pro, PitchBook, Bloomberg)
- Mobile app
- Pattern library / prediction engine (Phase 2)
- Historical data import beyond 30 days back (Phase 2)

---

## 7. User Journey

```
Mac starts in morning
      ↓
Daemon has been running overnight, ingesting signals
      ↓
8am: briefing job runs, Ollama synthesizes top signals
      ↓
Telegram message arrives: today's briefing in plain language
      ↓
Avinash reads it, clicks a link to open web UI for more detail
      ↓
Web UI shows full signal feed, entity explorer, historical graph
      ↓
Avinash asks a question ("what's happening with TSMC?") → entity query
      ↓
Over weeks: graph compounds, patterns become visible, understanding builds
```

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Ollama model quality too low for good briefings | Medium | Test Llama 3.2 vs Mistral; prompt engineering matters more than model size for classification |
| Free API rate limits hit | Medium | Stagger requests, cache aggressively, rotate sources |
| Neo4j setup complexity blocks early progress | Medium | Start with SQLite-only, add Neo4j in Phase 1b once ingestion is working |
| Signal volume too high = noise | High | Relevance scoring + domain filtering prevents firehose problem |
| Mac goes to sleep, daemon stops | Low | Use launchd plist to keep daemon alive |

---

## 9. Open Questions

- [ ] Which Ollama model gives best classification quality on a Mac Air (memory constraints matter)?
- [ ] Should the web UI be Next.js or simpler static HTML first?
- [ ] How to handle duplicate signals from multiple sources about the same event?
- [ ] What entity resolution strategy handles "Apple" vs "Apple Inc." vs "AAPL"?

---

## 10. Phase Roadmap

| Phase | Timeline | Key Deliverable |
|---|---|---|
| Phase 1 | Weeks 1-4 | Ingestion + SQLite + Ollama classification + Telegram daily briefing |
| Phase 1b | Weeks 5-6 | Neo4j graph integration + local web UI |
| Phase 2 | Weeks 7-12 | Historical data seeding + entity explorer + pattern detection |
| Phase 3 | Month 4+ | Claude API integration for deeper synthesis + friend sharing |
