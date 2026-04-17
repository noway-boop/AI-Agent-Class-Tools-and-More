"""News API connector — fetches Disney-related headlines from NewsAPI and Google News RSS."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List
from urllib.parse import quote_plus

from disney_dashboard.config.settings import NEWS_KEYWORDS
from disney_dashboard.ingestion.base import BaseConnector
from disney_dashboard.models.schemas import Signal, SourceType


class NewsAPIConnector(BaseConnector):
    source_type = SourceType.NEWS
    source_name = "newsapi"

    ENDPOINT = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: str, **kwargs) -> None:
        super().__init__(rate_limit=0.5, **kwargs)
        self.api_key = api_key

    async def fetch(self) -> List[Signal]:
        signals: List[Signal] = []
        query = " OR ".join(f'"{kw}"' for kw in NEWS_KEYWORDS[:5])
        from_date = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%d")

        data = await self._request(
            self.ENDPOINT,
            params={
                "q": query,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 100,
                "apiKey": self.api_key,
            },
        )

        for article in data.get("articles", []):
            published = article.get("publishedAt", "")
            try:
                pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pub_dt = datetime.utcnow()

            signals.append(
                Signal(
                    source_type=self.source_type,
                    source_name=self.source_name,
                    source_url=article.get("url", ""),
                    title=article.get("title", ""),
                    body=article.get("description", "") or "",
                    published_at=pub_dt,
                    raw_payload=article,
                )
            )
        self.logger.info("NewsAPI returned %d articles", len(signals))
        return signals


class GoogleNewsRSSConnector(BaseConnector):
    source_type = SourceType.NEWS
    source_name = "google_news_rss"

    BASE_URL = "https://news.google.com/rss/search"

    def __init__(self, **kwargs) -> None:
        super().__init__(rate_limit=0.3, **kwargs)

    async def fetch(self) -> List[Signal]:
        signals: List[Signal] = []

        for keyword in NEWS_KEYWORDS[:8]:
            url = f"{self.BASE_URL}?q={quote_plus(keyword)}&hl=en-US&gl=US&ceid=US:en"
            try:
                xml_text = await self._request_text(url)
                root = ET.fromstring(xml_text)
                channel = root.find("channel")
                if channel is None:
                    continue

                for item in channel.findall("item"):
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    pub_date_str = item.findtext("pubDate", "")

                    try:
                        pub_dt = datetime.strptime(
                            pub_date_str, "%a, %d %b %Y %H:%M:%S %Z"
                        )
                    except (ValueError, TypeError):
                        pub_dt = datetime.utcnow()

                    signals.append(
                        Signal(
                            source_type=self.source_type,
                            source_name=self.source_name,
                            source_url=link,
                            title=title,
                            body=item.findtext("description", "") or "",
                            published_at=pub_dt,
                            raw_payload={"keyword": keyword},
                        )
                    )
            except Exception as exc:
                self.logger.warning("Google News RSS failed for '%s': %s", keyword, exc)

        self.logger.info("Google News RSS returned %d items", len(signals))
        return signals
