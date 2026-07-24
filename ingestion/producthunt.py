import requests
from datetime import datetime, timezone
from ingestion.base import BaseIngester

# Product Hunt public GraphQL endpoint — no API key needed for basic post listing
PH_GRAPHQL_URL = "https://www.producthunt.com/frontend/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "tech-intel/1.0",
    "Accept": "application/json",
}
QUERY = """
{
  posts(order: VOTES, first: 20) {
    edges {
      node {
        id
        name
        tagline
        url
        votesCount
        createdAt
        topics {
          edges { node { name } }
        }
      }
    }
  }
}
"""


class ProductHuntIngester(BaseIngester):
    source_name = "producthunt"

    def fetch(self) -> list[dict]:
        try:
            resp = requests.post(
                PH_GRAPHQL_URL,
                json={"query": QUERY},
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            posts = data.get("data", {}).get("posts", {}).get("edges", [])
        except Exception as e:
            print(f"[producthunt] fetch error: {e}")
            return []

        signals = []
        for edge in posts:
            node = edge.get("node", {})
            topics = [t["node"]["name"] for t in node.get("topics", {}).get("edges", [])]
            body = node.get("tagline", "")
            if topics:
                body += f" — Topics: {', '.join(topics)}"
            signals.append({
                "source": self.source_name,
                "source_id": str(node["id"]),
                "title": f"[Product Hunt] {node['name']} — {node.get('tagline', '')}",
                "url": node.get("url"),
                "body": body[:500],
                "published_at": node.get("createdAt"),
            })
        return signals
