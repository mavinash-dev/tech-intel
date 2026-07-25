#!/usr/bin/env python3
"""Single-run ingestion + classification job. Called by GitHub Actions every 30 minutes."""
import sys
import traceback

print("[startup] importing db...", flush=True)
from db.schema import init_db

print("[startup] importing ingesters...", flush=True)
from ingestion.hackernews import HackerNewsIngester
from ingestion.reddit import RedditIngester
from ingestion.rss import RSSIngester
from ingestion.github_trending import GitHubTrendingIngester
from ingestion.devto import DevToIngester

print("[startup] importing classifier...", flush=True)
from classifier.gemini_classifier import run_classification_batch

print("[startup] all imports done.", flush=True)

INGESTERS = [
    HackerNewsIngester,
    RedditIngester,
    RSSIngester,
    GitHubTrendingIngester,
    DevToIngester,
]


def main():
    print("[main] starting ingest job...", flush=True)

    print("[main] init db...", flush=True)
    init_db()
    print("[main] db ready.", flush=True)

    total = 0
    for cls in INGESTERS:
        print(f"[main] running {cls.__name__}...", flush=True)
        try:
            n = cls().run()
            total += n
            print(f"[ingest] {cls.__name__}: +{n}", flush=True)
        except Exception as e:
            print(f"[ingest] {cls.__name__} failed: {e}", flush=True)
            traceback.print_exc()

    print(f"[ingest] total new signals: {total}", flush=True)

    print("[main] starting classification...", flush=True)
    try:
        run_classification_batch()
    except Exception as e:
        print(f"[main] classification failed: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

    print("[ingest] done.", flush=True)


if __name__ == "__main__":
    main()
