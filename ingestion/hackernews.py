import requests
from datetime import datetime, timezone
from ingestion.base import BaseIngester

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
FETCH_LIMIT = 30


class HackerNewsIngester(BaseIngester):
    source_name = "hackernews"

    def fetch(self) -> list:
        ids = requests.get(HN_TOP_URL, timeout=10).json()[:FETCH_LIMIT]
        signals = []
        for item_id in ids:
            try:
                item = requests.get(HN_ITEM_URL.format(item_id), timeout=10).json()
                if not item or item.get("type") != "story" or not item.get("title"):
                    continue
                signals.append({
                    "source": self.source_name,
                    "source_id": str(item["id"]),
                    "title": item["title"],
                    "url": item.get("url", f"https://news.ycombinator.com/item?id={item['id']}"),
                    "body": item.get("text", "")[:500] if item.get("text") else "",
                    "published_at": datetime.fromtimestamp(item["time"], tz=timezone.utc).isoformat(),
                })
            except Exception as e:
                print(f"[hackernews] item {item_id} error: {e}")
        return signals
