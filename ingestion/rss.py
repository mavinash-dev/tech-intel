import feedparser
from datetime import datetime
from email.utils import parsedate_to_datetime
from ingestion.base import BaseIngester

RSS_FEEDS = {
    "techcrunch":     "https://techcrunch.com/feed/",
    "mit_tech_review": "https://www.technologyreview.com/feed/",
    "arxiv_cs_ai":    "https://arxiv.org/rss/cs.AI",
    "arxiv_cs_lg":    "https://arxiv.org/rss/cs.LG",
    "tldr_tech":      "https://tldr.tech/api/rss/tech",
    "crunchbase_news": "https://news.crunchbase.com/feed/",
    "yc_blog":        "https://www.ycombinator.com/blog/rss.xml",
}

ENTRIES_PER_FEED = 20


def _parse_date(entry) -> str | None:
    if hasattr(entry, "published"):
        try:
            return parsedate_to_datetime(entry.published).isoformat()
        except Exception:
            pass
    if hasattr(entry, "updated"):
        try:
            return parsedate_to_datetime(entry.updated).isoformat()
        except Exception:
            pass
    return datetime.utcnow().isoformat()


class RSSIngester(BaseIngester):
    source_name = "rss"

    def fetch(self) -> list[dict]:
        signals = []
        for feed_key, feed_url in RSS_FEEDS.items():
            try:
                parsed = feedparser.parse(feed_url)
                for entry in parsed.entries[:ENTRIES_PER_FEED]:
                    source_id = entry.get("id") or entry.get("link", "")
                    title = entry.get("title", "").strip()
                    if not title or not source_id:
                        continue
                    body = entry.get("summary", "")[:500]
                    signals.append({
                        "source": f"rss_{feed_key}",
                        "source_id": source_id,
                        "title": title,
                        "url": entry.get("link"),
                        "body": body,
                        "published_at": _parse_date(entry),
                    })
            except Exception as e:
                print(f"[rss] {feed_key} error: {e}")
        return signals
