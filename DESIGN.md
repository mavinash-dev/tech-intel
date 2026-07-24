# Design Document
## tech-intel

**Version:** 0.1  
**Created:** 2026-07-25

---

## 1. Design Principles

1. **Explain everything** — Every signal shown in the UI has a plain-language explanation underneath it. Never show raw data without context. The user is building understanding, not just reading headlines.
2. **Signal over noise** — A curated, explained feed of 10 signals beats an overwhelming firehose of 100. Relevance score drives what surfaces. Domain filters let the user narrow focus.
3. **Compound over time** — The UI should make the graph's growth visible. Seeing "1,240 entities, 4,823 connections, 847 signals since Day 1" reinforces that the system is getting smarter every day.

---

## 2. User Flows

### Flow 1: Morning Briefing (Primary)
```
Phone buzzes → Telegram message arrives at 8am
      ↓
Read briefing: 5-7 signals explained in plain language
      ↓
[Optional] Tap link → opens web UI at localhost:3000
      ↓
Browse full signal feed, click entities to explore
      ↓
Done — understanding built passively
```
- **Entry point:** Telegram notification
- **Exit point:** Satisfied or opens web UI for deeper exploration
- **Key decision:** Briefing must be self-contained — readable without opening the web UI

### Flow 2: Active Exploration (Web UI)
```
Open localhost:3000
      ↓
See today's briefing at top
      ↓
Scroll signal feed (filterable by domain)
      ↓
Click entity (e.g. "NVIDIA") → entity detail page
      ↓
See all signals involving NVIDIA across time
      ↓
See connected entities (companies, technologies, countries NVIDIA links to)
```
- **Entry point:** Direct browser open or Telegram link
- **Exit point:** User satisfied, closes browser
- **Key decision:** Entity pages are the core "intelligence" view — this is where the graph shines

### Flow 3: Manual Query (Future — Phase 2)
```
Open web UI → Query box
      ↓
Type: "what's happening with AI infrastructure investment?"
      ↓
System queries Neo4j + sends context to Ollama
      ↓
Returns synthesized answer with source signals
```

---

## 3. Key Screens

### Screen: Home / Today's Briefing
- **Purpose:** Primary daily consumption — the thing you read every morning
- **Key elements:**
  - Date + "Today's Intelligence Briefing" header
  - 5-7 signal cards, each with: headline, domain tag (color-coded), plain explanation, entity tags
  - "One question worth sitting with today" — bottom of briefing
  - Graph stats bar: total entities, total signals, days running
- **User action:** Read, click entity tags to explore, scroll to signal feed below

### Screen: Signal Feed
- **Purpose:** Full list of ingested signals, filterable
- **Key elements:**
  - Domain filter tabs: All / Capital / Talent / Technology / Power / Infrastructure
  - Signal cards: title, source, time, domain tag, relevance score, plain explanation
  - Infinite scroll or pagination
- **User action:** Filter by domain, click signal to see full detail

### Screen: Entity Detail
- **Purpose:** Everything the system knows about one entity (company, person, technology)
- **Key elements:**
  - Entity name, type, country/category
  - Timeline of signals mentioning this entity (newest first)
  - Connected entities section: "Also appears with: TSMC, Nvidia, US CHIPS Act..."
  - Signal count, first seen date
- **User action:** Explore connections, understand entity's role in the ecosystem

### Screen: System Status (minimal)
- **Purpose:** Confirm the daemon is running and ingesting
- **Key elements:**
  - Last ingestion time
  - Signals ingested today
  - Ollama model status
  - Neo4j connection status
- **User action:** Glance — reassurance that the system is alive

---

## 4. Design Decisions

### Plain language first
- **Chose:** Every signal card shows Ollama-generated plain explanation by default, with original headline secondary
- **Because:** Avinash is building understanding, not just tracking news. Raw headlines without context are useless to someone new to the ecosystem.

### Domain color coding
- **Chose:** Color-coded domain tags across all views
- Capital → Green (money)
- Talent → Blue (people)
- Technology → Purple (product/tech)
- Power → Red (regulation/government)
- Infrastructure → Orange (physical layer)
- Narrative → Grey (media/opinion)
- **Because:** At a glance, you can see what type of signal this is before reading it

### No dark mode toggle (Phase 1) [ASSUMED]
- **Chose:** Dark theme by default (matches Avinash's dashboard project aesthetic)
- **Because:** Intelligence/analyst tools feel more serious in dark mode; simplifies Phase 1 by avoiding theme switching logic

---

## 5. Component Reference

| Component | Used In | Notes |
|---|---|---|
| SignalCard | Home, Feed | Shows domain tag, explanation, entity tags |
| EntityTag | SignalCard, EntityDetail | Clickable chip — navigates to entity page |
| DomainFilter | Feed | Tab group for filtering by domain |
| BriefingBlock | Home | Full morning briefing rendered as structured prose |
| GraphStatBar | Home | Live counts: entities, signals, days running |
| StatusIndicator | System Status | Green/red dot for daemon, Ollama, Neo4j health |

---

## 6. Design Resources

- Figma / wireframes: None (Phase 1 — build directly in code)
- Design system: Custom, minimal — dark background, clean typography
- Fonts: Inter (matches existing dashboard project) [ASSUMED]
- Colors: Dark bg (#0f0f0f), accent violet (#7c3aed — matches dashboard), domain colors as above
