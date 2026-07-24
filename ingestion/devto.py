import requests
from ingestion.base import BaseIngester

DEVTO_URL = "https://dev.to/api/articles"
TAGS = ["ai", "machinelearning", "programming", "webdev", "devops"]
PER_TAG = 10


class DevToIngester(BaseIngester):
    source_name = "devto"

    def fetch(self) -> list[dict]:
        signals = []
        for tag in TAGS:
            try:
                resp = requests.get(
                    DEVTO_URL,
                    params={"tag": tag, "per_page": PER_TAG, "top": 1},
                    timeout=10,
                )
                resp.raise_for_status()
                for article in resp.json():
                    signals.append({
                        "source": self.source_name,
                        "source_id": str(article["id"]),
                        "title": article["title"],
                        "url": article["url"],
                        "body": (article.get("description") or "")[:500],
                        "published_at": article.get("published_at"),
                    })
            except Exception as e:
                print(f"[devto] tag={tag} error: {e}")
        return signals
