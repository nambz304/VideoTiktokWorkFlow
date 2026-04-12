from pytrends.request import TrendReq
import praw
from typing import List
import logging

logger = logging.getLogger(__name__)

class TrendFetcher:
    def __init__(self, reddit_client_id: str, reddit_secret: str, reddit_user_agent: str):
        self.reddit = praw.Reddit(
            client_id=reddit_client_id,
            client_secret=reddit_secret,
            user_agent=reddit_user_agent,
        )

    def _fetch_google_trends(self, keywords: List[str], lang: str) -> List[dict]:
        try:
            hl = "vi-VN" if lang == "vi" else "en-US"
            geo = "VN" if lang == "vi" else "US"
            pytrends = TrendReq(hl=hl, tz=420)
            pytrends.build_payload(keywords[:5], timeframe="now 7-d", geo=geo)
            related = pytrends.related_queries()
            results = []
            for kw in keywords[:2]:
                df = related.get(kw, {}).get("top")
                if df is not None and not df.empty:
                    for _, row in df.head(5).iterrows():
                        results.append({
                            "topic": row["query"],
                            "score": int(row["value"]),
                            "source": "google_trends"
                        })
            return results
        except Exception as e:
            logger.warning(f"Google Trends fetch failed: {e}")
            return []

    def _fetch_reddit(self, lang: str) -> List[dict]:
        try:
            subreddits = ["health", "nutrition", "ArtificialIntelligence"] if lang == "en" else ["suckhoe"]
            results = []
            for sub in subreddits:
                try:
                    for post in self.reddit.subreddit(sub).hot(limit=5):
                        results.append({
                            "topic": post.title,
                            "score": min(100, post.score // 10),
                            "source": f"reddit/{sub}"
                        })
                except Exception:
                    continue
            return results
        except Exception as e:
            logger.warning(f"Reddit fetch failed: {e}")
            return []

    def fetch(self, keywords: List[str], lang: str = "vi", limit: int = 8) -> List[dict]:
        trends = self._fetch_google_trends(keywords, lang)
        reddit = self._fetch_reddit(lang)
        combined = trends + reddit
        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:limit]
