"""Twitter/X connector — searches for Disney-related tweets via the v2 API."""

from __future__ import annotations

from datetime import datetime
from typing import List

from disney_dashboard.config.settings import NEWS_KEYWORDS
from disney_dashboard.ingestion.base import BaseConnector
from disney_dashboard.models.schemas import Signal, SourceType


class TwitterConnector(BaseConnector):
    source_type = SourceType.TWITTER
    source_name = "twitter"

    SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

    def __init__(self, bearer_token: str, **kwargs) -> None:
        super().__init__(rate_limit=0.3, **kwargs)
        self.bearer_token = bearer_token

    async def fetch(self) -> List[Signal]:
        signals: List[Signal] = []
        query_terms = [f'"{kw}"' for kw in NEWS_KEYWORDS[:4]]
        query = f"({' OR '.join(query_terms)}) lang:en -is:retweet"

        if len(query) > 512:
            query = query[:510]

        try:
            data = await self._request(
                self.SEARCH_URL,
                headers={"Authorization": f"Bearer {self.bearer_token}"},
                params={
                    "query": query,
                    "max_results": 100,
                    "tweet.fields": "created_at,public_metrics,author_id,lang",
                    "expansions": "author_id",
                    "user.fields": "username,name,public_metrics",
                },
            )

            users_map = {}
            for user in data.get("includes", {}).get("users", []):
                users_map[user["id"]] = user

            for tweet in data.get("data", []):
                created_str = tweet.get("created_at", "")
                try:
                    pub_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pub_dt = datetime.utcnow()

                author_id = tweet.get("author_id", "")
                author = users_map.get(author_id, {})
                metrics = tweet.get("public_metrics", {})

                signals.append(
                    Signal(
                        source_type=self.source_type,
                        source_name=self.source_name,
                        source_url=f"https://twitter.com/i/status/{tweet['id']}",
                        title=tweet.get("text", "")[:200],
                        body=tweet.get("text", ""),
                        published_at=pub_dt,
                        raw_payload={
                            "tweet_id": tweet["id"],
                            "author_username": author.get("username", ""),
                            "author_name": author.get("name", ""),
                            "author_followers": author.get("public_metrics", {}).get(
                                "followers_count", 0
                            ),
                            "retweet_count": metrics.get("retweet_count", 0),
                            "like_count": metrics.get("like_count", 0),
                            "reply_count": metrics.get("reply_count", 0),
                            "impression_count": metrics.get("impression_count", 0),
                        },
                    )
                )
        except Exception as exc:
            self.logger.warning("Twitter search failed: %s", exc)

        self.logger.info("Twitter returned %d tweets", len(signals))
        return signals
