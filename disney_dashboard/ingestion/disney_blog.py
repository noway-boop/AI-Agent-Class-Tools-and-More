"""Disney Parks Blog RSS connector — official Disney announcements."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List

from disney_dashboard.ingestion.base import BaseConnector
from disney_dashboard.models.schemas import Signal, SourceType


class DisneyBlogConnector(BaseConnector):
    source_type = SourceType.DISNEY_BLOG
    source_name = "disney_parks_blog"

    FEEDS = [
        "https://disneyparks.disney.go.com/blog/feed/",
        "https://disneyworld.disney.go.com/blog/feed/",
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(rate_limit=0.2, **kwargs)

    async def fetch(self) -> List[Signal]:
        signals: List[Signal] = []

        for feed_url in self.FEEDS:
            try:
                xml_text = await self._request_text(feed_url)
                signals.extend(self._parse_rss(xml_text, feed_url))
            except Exception as exc:
                self.logger.warning("Disney Blog RSS failed for %s: %s", feed_url, exc)

        self.logger.info("Disney Blog returned %d posts", len(signals))
        return signals

    def _parse_rss(self, xml_text: str, feed_url: str) -> List[Signal]:
        signals: List[Signal] = []
        root = ET.fromstring(xml_text)

        ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
        channel = root.find("channel")
        if channel is None:
            return signals

        for item in channel.findall("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date_str = item.findtext("pubDate", "")
            description = item.findtext("description", "") or ""
            content_encoded = item.findtext("content:encoded", "", ns) or ""
            categories = [c.text for c in item.findall("category") if c.text]

            try:
                pub_dt = datetime.strptime(
                    pub_date_str, "%a, %d %b %Y %H:%M:%S %z"
                )
            except (ValueError, TypeError):
                pub_dt = datetime.utcnow()

            body = content_encoded[:3000] if content_encoded else description[:3000]

            signals.append(
                Signal(
                    source_type=self.source_type,
                    source_name=self.source_name,
                    source_url=link,
                    title=title,
                    body=body,
                    published_at=pub_dt,
                    raw_payload={
                        "feed_url": feed_url,
                        "categories": categories,
                    },
                )
            )

        return signals
