"""Reddit connector — fetches posts from Disney-related subreddits."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from disney_dashboard.config.settings import TRACKED_SUBREDDITS
from disney_dashboard.ingestion.base import BaseConnector
from disney_dashboard.models.schemas import Signal, SourceType


class RedditConnector(BaseConnector):
    source_type = SourceType.REDDIT
    source_name = "reddit"

    AUTH_URL = "https://www.reddit.com/api/v1/access_token"
    BASE_URL = "https://oauth.reddit.com"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str = "DisneyDashboard/0.1",
        **kwargs,
    ) -> None:
        super().__init__(rate_limit=1.0, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self._access_token: Optional[str] = None

    async def _authenticate(self) -> str:
        import aiohttp
        import base64

        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.AUTH_URL,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "User-Agent": self.user_agent,
                },
                data={"grant_type": "client_credentials"},
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                self._access_token = data["access_token"]
                return self._access_token

    async def fetch(self) -> List[Signal]:
        if not self._access_token:
            await self._authenticate()

        signals: List[Signal] = []
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "User-Agent": self.user_agent,
        }

        for subreddit in TRACKED_SUBREDDITS:
            try:
                data = await self._request(
                    f"{self.BASE_URL}/r/{subreddit}/hot",
                    headers=headers,
                    params={"limit": 50},
                )

                for post in data.get("data", {}).get("children", []):
                    post_data = post.get("data", {})
                    created_utc = post_data.get("created_utc", 0)
                    pub_dt = datetime.utcfromtimestamp(created_utc)

                    signals.append(
                        Signal(
                            source_type=self.source_type,
                            source_name=f"r/{subreddit}",
                            source_url=f"https://reddit.com{post_data.get('permalink', '')}",
                            title=post_data.get("title", ""),
                            body=post_data.get("selftext", "")[:2000],
                            published_at=pub_dt,
                            raw_payload={
                                "subreddit": subreddit,
                                "score": post_data.get("score", 0),
                                "num_comments": post_data.get("num_comments", 0),
                                "upvote_ratio": post_data.get("upvote_ratio", 0),
                                "author": post_data.get("author", ""),
                                "link_flair_text": post_data.get("link_flair_text", ""),
                            },
                        )
                    )
            except Exception as exc:
                self.logger.warning("Reddit fetch failed for r/%s: %s", subreddit, exc)

        self.logger.info("Reddit returned %d posts", len(signals))
        return signals
