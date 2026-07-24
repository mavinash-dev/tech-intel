# Project Status
## tech-intel

<!-- DASHBOARD_META
name: tech-intel
slug: tech-intel
status: Active
phase: Phase 1
started: 2026-07-25
last_updated: 2026-07-25
summary: Local signal intelligence system — ingests global tech signals, builds a knowledge graph, delivers plain-language briefings via Telegram and web
current_focus: Project foundation complete — setting up Python ingestion daemon and SQLite schema
-->

---

## Current Phase
**Phase 1** — Core ingestion, AI classification, and daily Telegram briefing

## Status
`Active`

---

## Current Focus
Project foundation documents created. Next: scaffold Python project structure, set up SQLite schema, and build the first ingestion source (Hacker News).

---

## Development Log

### 2026-07-25 — Session 1
**Done:**
- [x] Full brainstorm — defined what the system is (signal intelligence, not news aggregator)
- [x] Defined scope: local Mac, Ollama only (Phase 1), Telegram + web delivery, max 3 users
- [x] Created project foundation: PRD, ARCH, DESIGN, STATUS, CLAUDE.md, README
- [x] Cloned empty GitHub repo: mavinash-dev/tech-intel

**Decisions:**
- Ollama-only in Phase 1 (Claude API slot reserved for Phase 3)
- SQLite first, Neo4j added in Phase 1b once ingestion is stable
- Telegram over WhatsApp (WhatsApp requires paid Meta API)
- launchd for daemon persistence on Mac

**Time:** 1h

---

## Pending Tasks

### Phase 1a — Ingestion + Classification
- [ ] Scaffold Python project structure (pyproject.toml / requirements.txt) — est: 30min
- [ ] SQLite schema setup (signals_raw + signals_enriched tables) — est: 1h
- [ ] Hacker News ingestion source — est: 1h
- [ ] Reddit ingestion source (r/technology, r/programming, r/MachineLearning) — est: 1h
- [ ] RSS ingestion sources (TechCrunch, MIT Tech Review, arXiv CS) — est: 1h
- [ ] GitHub Trending ingestion — est: 1h
- [ ] Ollama classification pipeline (domain, entities, explanation, relevance score) — est: 3h
- [ ] Deduplication logic (source_id based) — est: 1h
- [ ] APScheduler daemon setup (30-min polling) — est: 1h
- [ ] launchd plist for Mac auto-start — est: 30min

### Phase 1b — Briefing + Delivery
- [ ] Daily briefing generator (Ollama synthesis of top signals) — est: 2h
- [ ] Telegram bot setup + delivery at 8am — est: 1h
- [ ] FastAPI server with /signals, /briefing, /entity endpoints — est: 2h

### Phase 1c — Web UI
- [ ] Next.js app scaffold — est: 1h
- [ ] Home screen: today's briefing — est: 2h
- [ ] Signal feed with domain filters — est: 2h
- [ ] Entity detail page — est: 2h
- [ ] System status screen — est: 1h

### Phase 1d — Graph (Neo4j)
- [ ] Neo4j Desktop setup + connection — est: 1h
- [ ] Entity extraction → graph write pipeline — est: 3h
- [ ] Basic Cypher queries for entity explorer — est: 2h

### Phase 2 (future)
- [ ] Historical data seeding (30-90 days back)
- [ ] Pattern detection across signal history
- [ ] Claude API integration for deeper synthesis
- [ ] Friend sharing / export

---

## Blockers
- None

---

## Time Tracker

| Date | Session | Hours | Cumulative |
|---|---|---|---|
| 2026-07-25 | Brainstorm + Foundation setup | 1h | 1h |

---

## Key Decisions Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-25 | Ollama-only for Phase 1 | No API key needed, fully free and local |
| 2026-07-25 | SQLite before Neo4j | Zero-config start, graph added once ingestion is stable |
| 2026-07-25 | Telegram over WhatsApp | WhatsApp Business API is paid; Telegram is free |
| 2026-07-25 | launchd for daemon | Native macOS, survives sleep/reboot, no Docker needed |
