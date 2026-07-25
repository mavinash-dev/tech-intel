#!/usr/bin/env python3
"""Single-run ingestion + classification job. Called by GitHub Actions every 30 minutes."""
import sys
from db.schema import init_db
from ingestion.hackernews import HackerNewsIngester
from ingestion.reddit import RedditIngester
from ingestion.rss import RSSIngester
from ingestion.github_trending import GitHubTrendingIngester
from ingestion.devto import DevToIngester
from classifier.gemini_classifier import run_classification_batch

INGESTERS = [
    HackerNewsIngester,
    RedditIngester,
    RSSIngester,
    GitHubTrendingIngester,
    DevToIngester,
]


def main():
    init_db()
    total = 0
    for cls in INGESTERS:
        try:
            n = cls().run()
            total += n
            print(f"[ingest] {cls.__name__}: +{n}")
        except Exception as e:
            print(f"[ingest] {cls.__name__} failed: {e}", file=sys.stderr)

    print(f"[ingest] total new signals: {total}")
    run_classification_batch(batch_size=50)
    print("[ingest] done.")


if __name__ == "__main__":
    main()
