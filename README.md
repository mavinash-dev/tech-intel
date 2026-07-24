# tech-intel

> A local intelligence system that ingests global tech signals, builds a connected knowledge graph over time, and delivers analyst-grade briefings — running entirely on your Mac.

---

## What It Is

Tech Intel is a personal signal intelligence system for someone who wants to understand the global technology ecosystem — not just what launched today, but why investment is flowing somewhere, what a company's layoff actually signals, and what pattern from 2019 is quietly repeating right now. It ingests continuously from free sources, classifies signals using a local AI model, builds a Neo4j knowledge graph linking companies, events, and technologies across time, and delivers plain-language briefings to a local web app and Telegram.

---

## Why It Exists

Most tech news is surface-level: new SDK released, startup raised money, company fired engineers. The real signal — where capital is actually flowing, which talent movements predict market shifts, what regulatory changes mean for infrastructure — is scattered across dozens of sources and requires cross-domain pattern recognition to interpret. This system connects those dots automatically and explains them plainly.

---

## Status

**Phase:** Phase 1 — Core ingestion, graph, and daily briefing  
**Stage:** Early Development

---

## Tech Stack

- **Python** — background daemon, ingestion, AI orchestration
- **SQLite** — raw signal store before graph processing
- **Neo4j Desktop** — local knowledge graph (entities + relationships across time)
- **Ollama + Llama 3** — local LLM for signal classification and briefing synthesis (free, no API key)
- **FastAPI** — local web server and query API
- **Next.js** — local web UI for browsing signals and reading briefings
- **Telegram Bot API** — delivers daily briefings to phone (free)

---

## Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama (must be installed separately)
ollama serve

# 3. Pull the model
ollama pull llama3.2

# 4. Start Neo4j Desktop (install separately, free)
# Create a local database called "tech-intel"

# 5. Run the ingestion daemon
python daemon.py

# 6. Start the web server
uvicorn api:app --reload --port 8000

# 7. Start the web UI
cd web && npm install && npm run dev
# Open http://localhost:3000
```

---

## Project Docs

| Document | Purpose |
|---|---|
| [PRD.md](PRD.md) | Product requirements and feature spec |
| [ARCH.md](ARCH.md) | Technical architecture and data model |
| [DESIGN.md](DESIGN.md) | UX flows and interface design |
| [STATUS.md](STATUS.md) | Development log and pending tasks |
| [CLAUDE.md](CLAUDE.md) | Full project brief for AI-assisted sessions |
