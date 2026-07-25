"""
Manually trigger a briefing right now.
  python send_now.py           — ingest + generate + send to Telegram
  python send_now.py --open    — ingest + generate + open in browser only
  python send_now.py --skip-ingest  — skip ingestion, just re-render last DB state
"""
import sys
import subprocess

skip_ingest = "--skip-ingest" in sys.argv

if not skip_ingest:
    print("[send_now] running ingestion first...")
    from db.schema import init_db
    from classifier.ollama_classifier import run_classification_batch
    from ingestion.hackernews import HackerNewsIngester
    from ingestion.reddit import RedditIngester
    from ingestion.rss import RSSIngester
    from ingestion.github_trending import GitHubTrendingIngester
    from ingestion.devto import DevToIngester
    from ingestion.producthunt import ProductHuntIngester

    init_db()
    total = 0
    for ingester in [
        HackerNewsIngester(), RedditIngester(), RSSIngester(),
        GitHubTrendingIngester(), DevToIngester(), ProductHuntIngester(),
    ]:
        total += ingester.run()
    print(f"[send_now] ingested {total} new signals")
    run_classification_batch(batch_size=30)
    print("[send_now] classification done")

from briefing.generator import generate_briefing
from briefing.telegram import send_briefing

path, signals = generate_briefing()
print(f"Briefing saved: {path}")

if "--open" in sys.argv:
    subprocess.run(["open", path])
else:
    subprocess.run(["open", path])
    ok = send_briefing(path, signals)
    print("Sent to Telegram ✓" if ok else "Send failed — check .env")
