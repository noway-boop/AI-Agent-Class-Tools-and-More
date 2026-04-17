"""YouTube Data API connector — tracks Disney vlogger channels and search results."""

from __future__ import annotations

from datetime import datetime
from typing import List

from disney_dashboard.config.settings import NEWS_KEYWORDS, TRACKED_YOUTUBE_CHANNELS
from disney_dashboard.ingestion.base import BaseConnector
from disney_dashboard.models.schemas import Signal, SourceType


class YouTubeConnector(BaseConnector):
    source_type = SourceType.YOUTUBE
    source_name = "youtube"

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str, **kwargs) -> None:
        super().__init__(rate_limit=0.5, **kwargs)
        self.api_key = api_key

    async def fetch(self) -> List[Signal]:
        signals: List[Signal] = []
        signals.extend(await self._fetch_channel_videos())
        signals.extend(await self._fetch_search_results())
        self.logger.info("YouTube returned %d videos total", len(signals))
        return signals

    async def _fetch_channel_videos(self) -> List[Signal]:
        signals: List[Signal] = []

        for channel_id, channel_name in TRACKED_YOUTUBE_CHANNELS.items():
            try:
                data = await self._request(
                    f"{self.BASE_URL}/search",
                    params={
                        "key": self.api_key,
                        "channelId": channel_id,
                        "part": "snippet",
                        "order": "date",
                        "maxResults": 10,
                        "type": "video",
                    },
                )

                for item in data.get("items", []):
                    snippet = item.get("snippet", {})
                    video_id = item.get("id", {}).get("videoId", "")
                    pub_str = snippet.get("publishedAt", "")

                    try:
                        pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pub_dt = datetime.utcnow()

                    signals.append(
                        Signal(
                            source_type=self.source_type,
                            source_name=f"youtube:{channel_name}",
                            source_url=f"https://www.youtube.com/watch?v={video_id}",
                            title=snippet.get("title", ""),
                            body=snippet.get("description", "")[:1500],
                            published_at=pub_dt,
                            raw_payload={
                                "channel_id": channel_id,
                                "channel_name": channel_name,
                                "video_id": video_id,
                                "thumbnail": snippet.get("thumbnails", {})
                                .get("high", {})
                                .get("url", ""),
                            },
                        )
                    )
            except Exception as exc:
                self.logger.warning(
                    "YouTube channel fetch failed for %s: %s", channel_name, exc
                )

        return signals

    async def _fetch_search_results(self) -> List[Signal]:
        signals: List[Signal] = []
        query = " | ".join(NEWS_KEYWORDS[:3])

        try:
            data = await self._request(
                f"{self.BASE_URL}/search",
                params={
                    "key": self.api_key,
                    "q": query,
                    "part": "snippet",
                    "order": "date",
                    "maxResults": 25,
                    "type": "video",
                    "relevanceLanguage": "en",
                },
            )

            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId", "")
                pub_str = snippet.get("publishedAt", "")

                try:
                    pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pub_dt = datetime.utcnow()

                signals.append(
                    Signal(
                        source_type=self.source_type,
                        source_name="youtube:search",
                        source_url=f"https://www.youtube.com/watch?v={video_id}",
                        title=snippet.get("title", ""),
                        body=snippet.get("description", "")[:1500],
                        published_at=pub_dt,
                        raw_payload={
                            "video_id": video_id,
                            "channel_title": snippet.get("channelTitle", ""),
                            "search_query": query,
                        },
                    )
                )
        except Exception as exc:
            self.logger.warning("YouTube search failed: %s", exc)

        return signals
