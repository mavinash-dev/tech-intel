import requests
from datetime import datetime
from bs4 import BeautifulSoup
from ingestion.base import BaseIngester

TRENDING_URL = "https://github.com/trending"
HEADERS = {"User-Agent": "tech-intel/1.0"}


class GitHubTrendingIngester(BaseIngester):
    source_name = "github_trending"

    def fetch(self) -> list[dict]:
        resp = requests.get(TRENDING_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        signals = []
        today = datetime.utcnow().date().isoformat()

        for repo in soup.select("article.Box-row"):
            try:
                name_tag = repo.select_one("h2 a")
                if not name_tag:
                    continue
                full_name = name_tag.get("href", "").strip("/")
                description_tag = repo.select_one("p")
                description = description_tag.get_text(strip=True) if description_tag else ""
                lang_tag = repo.select_one("[itemprop='programmingLanguage']")
                language = lang_tag.get_text(strip=True) if lang_tag else ""
                stars_tag = repo.select_one("a[href$='/stargazers']")
                stars = stars_tag.get_text(strip=True).replace(",", "") if stars_tag else ""

                title = f"[GitHub Trending] {full_name}"
                if language:
                    title += f" ({language})"
                body = description
                if stars:
                    body += f" — {stars} stars"

                signals.append({
                    "source": self.source_name,
                    "source_id": f"{full_name}_{today}",
                    "title": title,
                    "url": f"https://github.com/{full_name}",
                    "body": body[:500],
                    "published_at": today,
                })
            except Exception as e:
                print(f"[github_trending] repo parse error: {e}")

        return signals
