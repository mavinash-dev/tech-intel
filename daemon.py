"""
Entry point. Run with: python daemon.py
Ingests all sources every 30 min, classifies after each run.
"""
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from db.schema import init_db
from config import INGESTION_INTERVAL_MINUTES, BRIEFING_HOUR
from briefing.generator import generate_briefing
from briefing.telegram import send_briefing
from ingestion.hackernews import HackerNewsIngester
from ingestion.reddit import RedditIngester
from ingestion.rss import RSSIngester
from ingestion.github_trending import GitHubTrendingIngester
from ingestion.devto import DevToIngester
from ingestion.producthunt import ProductHuntIngester
from classifier.ollama_classifier import run_classification_batch

INGESTERS = [
    HackerNewsIngester(),
    RedditIngester(),
    RSSIngester(),
    GitHubTrendingIngester(),
    DevToIngester(),
    ProductHuntIngester(),
]


def run_ingestion():
    print("\n[daemon] === ingestion cycle start ===")
    total = 0
    for ingester in INGESTERS:
        total += ingester.run()
    print(f"[daemon] ingestion complete — {total} new signals total")
    run_classification_batch(batch_size=30)
    print("[daemon] === cycle complete ===\n")


def run_briefing():
    print("\n[daemon] === briefing generation start ===")
    text = generate_briefing()
    print(text[:500] + "...\n")
    send_briefing(text)
    print("[daemon] === briefing complete ===\n")


def main():
    print("[daemon] starting tech-intel...")
    init_db()

    # Run once immediately on start
    run_ingestion()

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_ingestion,
        trigger=IntervalTrigger(minutes=INGESTION_INTERVAL_MINUTES),
        id="ingestion",
        name="Signal ingestion + classification",
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_job(
        run_briefing,
        trigger=IntervalTrigger(hours=1),
        id="briefing",
        name="Hourly briefing generation + Telegram delivery",
        max_instances=1,
        coalesce=True,
    )

    print(f"[daemon] scheduler running — ingestion every {INGESTION_INTERVAL_MINUTES}min, briefing every 1h")
    print("[daemon] press Ctrl+C to stop\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n[daemon] stopped.")


if __name__ == "__main__":
    main()
