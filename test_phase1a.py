"""
Phase 1a smoke tests. Run with: python test_phase1a.py
Tests real network calls and real Ollama — no mocks.
Each test prints PASS / FAIL / SKIP with a reason.
"""
import json
import os
import tempfile
import sys

# ── helpers ──────────────────────────────────────────────────────────────────

PASS  = "\033[92m  PASS\033[0m"
FAIL  = "\033[91m  FAIL\033[0m"
SKIP  = "\033[93m  SKIP\033[0m"
results = []

def check(name, passed, note=""):
    tag = PASS if passed else FAIL
    line = f"{tag}  {name}"
    if note:
        line += f"  ({note})"
    print(line)
    results.append((name, passed))

def skip(name, reason):
    print(f"{SKIP}  {name}  ({reason})")
    results.append((name, None))


# ── override DB_PATH so tests don't touch the real DB ────────────────────────
os.environ.setdefault("DB_PATH", ":memory:")
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DB_PATH"] = _tmp_db.name

# ── 1. Config loads ──────────────────────────────────────────────────────────
print("\n── Config ──────────────────────────────────────────")
try:
    import config
    check("config loads", True, f"DB_PATH={config.DB_PATH}")
except Exception as e:
    check("config loads", False, str(e))

# ── 2. DB schema ─────────────────────────────────────────────────────────────
print("\n── Database ─────────────────────────────────────────")
try:
    from db.schema import init_db
    init_db()
    check("db init (creates tables)", True)
except Exception as e:
    check("db init", False, str(e))

try:
    from db.connection import get_connection
    conn = get_connection()
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    for t in ["signals_raw", "signals_enriched", "predictions"]:
        check(f"table exists: {t}", t in tables)
    conn.close()
except Exception as e:
    check("table check", False, str(e))

# ── 3. Deduplication ─────────────────────────────────────────────────────────
print("\n── Deduplication ────────────────────────────────────")
try:
    from ingestion.hackernews import HackerNewsIngester
    ingester = HackerNewsIngester()
    dummy = [{
        "source": "test", "source_id": "dup-001",
        "title": "Duplicate test signal", "url": "https://example.com",
        "body": "test body", "published_at": "2026-07-25T08:00:00",
    }]
    first  = ingester.save(dummy)
    second = ingester.save(dummy)
    check("dedup: first insert saves 1", first == 1, f"got {first}")
    check("dedup: second insert saves 0", second == 0, f"got {second}")
except Exception as e:
    check("dedup", False, str(e))

# ── 4. Hacker News ───────────────────────────────────────────────────────────
print("\n── Ingestion Sources ────────────────────────────────")
try:
    from ingestion.hackernews import HackerNewsIngester
    signals = HackerNewsIngester().fetch()
    check("hackernews fetch", len(signals) > 0, f"{len(signals)} signals")
    if signals:
        s = signals[0]
        check("hackernews signal has required fields",
              all(k in s for k in ["source", "source_id", "title"]),
              f"title: {s.get('title', '')[:60]}")
except Exception as e:
    check("hackernews", False, str(e))

# ── 5. RSS ───────────────────────────────────────────────────────────────────
try:
    from ingestion.rss import RSSIngester
    signals = RSSIngester().fetch()
    sources = {s["source"] for s in signals}
    check("rss fetch", len(signals) > 0, f"{len(signals)} signals from {len(sources)} feeds")
except Exception as e:
    check("rss", False, str(e))

# ── 6. GitHub Trending ───────────────────────────────────────────────────────
try:
    from ingestion.github_trending import GitHubTrendingIngester
    signals = GitHubTrendingIngester().fetch()
    check("github trending fetch", len(signals) > 0, f"{len(signals)} repos")
except Exception as e:
    check("github trending", False, str(e))

# ── 7. Dev.to ────────────────────────────────────────────────────────────────
try:
    from ingestion.devto import DevToIngester
    signals = DevToIngester().fetch()
    check("devto fetch", len(signals) > 0, f"{len(signals)} signals")
except Exception as e:
    check("devto", False, str(e))

# ── 8. Reddit ────────────────────────────────────────────────────────────────
try:
    import config as _cfg
    if not _cfg.REDDIT_CLIENT_ID:
        skip("reddit", "REDDIT_CLIENT_ID not set in .env — set it to test Reddit")
    else:
        from ingestion.reddit import RedditIngester
        signals = RedditIngester().fetch()
        check("reddit fetch", len(signals) > 0, f"{len(signals)} signals")
except Exception as e:
    check("reddit", False, str(e))

# ── 9. Product Hunt ──────────────────────────────────────────────────────────
try:
    from ingestion.producthunt import ProductHuntIngester
    signals = ProductHuntIngester().fetch()
    # PH GraphQL endpoint sometimes returns empty or rejects — treat as soft failure
    if len(signals) == 0:
        skip("producthunt", "0 results — PH GraphQL may require auth. Will be confirmed on first live run.")
    else:
        check("producthunt fetch", True, f"{len(signals)} signals")
except Exception as e:
    skip("producthunt", f"PH GraphQL error: {e}")

# ── 10. Ollama classifier ────────────────────────────────────────────────────
print("\n── Ollama Classifier ────────────────────────────────")
try:
    import ollama as _ollama
    import config as _cfg
    client = _ollama.Client(host=_cfg.OLLAMA_HOST)
    models = [m.model for m in client.list().models]
    model_present = any(_cfg.OLLAMA_MODEL in m for m in models)
    check(f"ollama: model {_cfg.OLLAMA_MODEL} available", model_present,
          f"installed models: {', '.join(models) or 'none'}")
except Exception as e:
    skip("ollama connectivity", f"Ollama not running or not installed: {e}")
    model_present = False

if model_present:
    try:
        from classifier.ollama_classifier import classify_signal
        result = classify_signal(
            raw_id=0,
            title="OpenAI raises $6.6 billion in funding at $157 billion valuation",
            source="hackernews",
            body="OpenAI has closed a $6.6 billion funding round led by Thrive Capital, "
                 "valuing the company at $157 billion.",
            url="https://example.com",
        )
        check("classifier returns result", result is not None)
        if result:
            check("classifier: domain field present",   "domain" in result, result.get("domain"))
            check("classifier: relevance_score 0-1",    0 <= result.get("relevance_score", -1) <= 1,
                  str(result.get("relevance_score")))
            check("classifier: plain_explanation present", bool(result.get("plain_explanation")))
            check("classifier: entities is list",       isinstance(result.get("entities"), list),
                  f"{len(result.get('entities', []))} entities")
            print(f"\n  Sample output:")
            print(f"  Domain:      {result.get('domain')}")
            print(f"  Score:       {result.get('relevance_score')}")
            print(f"  Explanation: {result.get('plain_explanation', '')[:120]}...")
            print(f"  Entities:    {[e['name'] for e in result.get('entities', [])]}")
            print(f"  Prediction:  {result.get('prediction', '')[:100]}")
    except Exception as e:
        check("classifier run", False, str(e))

# ── Summary ──────────────────────────────────────────────────────────────────
print("\n── Summary ──────────────────────────────────────────")
passed  = sum(1 for _, r in results if r is True)
failed  = sum(1 for _, r in results if r is False)
skipped = sum(1 for _, r in results if r is None)
total   = passed + failed

print(f"  {passed}/{total} passed  |  {failed} failed  |  {skipped} skipped\n")

os.unlink(_tmp_db.name)

if failed > 0:
    sys.exit(1)
