import praw
from datetime import datetime, timezone
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
from ingestion.base import BaseIngester

SUBREDDITS = ["technology", "programming", "MachineLearning", "artificial", "singularity"]
POSTS_PER_SUB = 15


class RedditIngester(BaseIngester):
    source_name = "reddit"

    def fetch(self) -> list:
        if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
            print("[reddit] skipped — REDDIT_CLIENT_ID/SECRET not set in .env")
            return []

        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
        signals = []
        for sub_name in SUBREDDITS:
            try:
                for post in reddit.subreddit(sub_name).hot(limit=POSTS_PER_SUB):
                    if post.stickied:
                        continue
                    signals.append({
                        "source": self.source_name,
                        "source_id": post.id,
                        "title": post.title,
                        "url": post.url,
                        "body": (post.selftext[:500] if post.selftext else ""),
                        "published_at": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
                    })
            except Exception as e:
                print(f"[reddit] r/{sub_name} error: {e}")
        return signals
