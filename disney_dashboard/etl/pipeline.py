"""ETL pipeline orchestrator — coordinates ingestion, processing, and storage."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from disney_dashboard.config.settings import load_config
from disney_dashboard.ingestion.base import BaseConnector
from disney_dashboard.ingestion.disney_blog import DisneyBlogConnector
from disney_dashboard.ingestion.news import GoogleNewsRSSConnector, NewsAPIConnector
from disney_dashboard.ingestion.park_wait_times import ParkWaitTimesConnector
from disney_dashboard.ingestion.reddit import RedditConnector
from disney_dashboard.ingestion.sec_filings import SECEdgarConnector
from disney_dashboard.ingestion.twitter import TwitterConnector
from disney_dashboard.ingestion.youtube import YouTubeConnector
from disney_dashboard.models.schemas import IngestionResult, Signal
from disney_dashboard.processing.dedup import DeduplicationEngine
from disney_dashboard.processing.entity_resolver import EntityMatch, EntityResolver
from disney_dashboard.processing.normalizer import SignalNormalizer
from disney_dashboard.utils.logging import get_logger

logger = get_logger("pipeline")


@dataclass
class PipelineResult:
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    total_signals_fetched: int = 0
    total_signals_after_dedup: int = 0
    total_entity_matches: int = 0
    source_results: List[IngestionResult] = field(default_factory=list)
    signals: List[Signal] = field(default_factory=list)
    entity_map: Dict[str, List[EntityMatch]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class ETLPipeline:
    def __init__(self) -> None:
        self.api_config, self.db_config, self.ingestion_config = load_config()
        self.dedup = DeduplicationEngine()
        self.normalizer = SignalNormalizer()
        self.entity_resolver = EntityResolver()

    def _build_connectors(self) -> List[BaseConnector]:
        connectors: List[BaseConnector] = []

        connectors.append(SECEdgarConnector())
        connectors.append(DisneyBlogConnector())
        connectors.append(ParkWaitTimesConnector())
        connectors.append(GoogleNewsRSSConnector())

        if self.api_config.news_api_key:
            connectors.append(NewsAPIConnector(api_key=self.api_config.news_api_key))

        if self.api_config.reddit_client_id and self.api_config.reddit_client_secret:
            connectors.append(
                RedditConnector(
                    client_id=self.api_config.reddit_client_id,
                    client_secret=self.api_config.reddit_client_secret,
                    user_agent=self.api_config.reddit_user_agent,
                )
            )

        if self.api_config.youtube_api_key:
            connectors.append(
                YouTubeConnector(api_key=self.api_config.youtube_api_key)
            )

        if self.api_config.twitter_bearer_token:
            connectors.append(
                TwitterConnector(bearer_token=self.api_config.twitter_bearer_token)
            )

        return connectors

    async def run(self, sources: Optional[List[str]] = None) -> PipelineResult:
        result = PipelineResult()
        start = time.monotonic()

        logger.info("=== ETL Pipeline starting ===")

        connectors = self._build_connectors()
        if sources:
            connectors = [c for c in connectors if c.source_name in sources]

        logger.info("Running %d connectors", len(connectors))

        # Phase 1: Parallel ingestion
        all_signals: List[Signal] = []
        ingestion_tasks = [connector.run() for connector in connectors]
        ingestion_results = await asyncio.gather(*ingestion_tasks, return_exceptions=True)

        for i, res in enumerate(ingestion_results):
            if isinstance(res, Exception):
                error_msg = f"{connectors[i].source_name}: {res}"
                result.errors.append(error_msg)
                logger.error("Connector failed: %s", error_msg)
                continue
            result.source_results.append(res)

        # Collect signals from successful connectors
        for connector in connectors:
            try:
                signals = await connector.fetch()
                all_signals.extend(signals)
            except Exception as exc:
                logger.warning("Signal collection from %s failed: %s", connector.source_name, exc)

        result.total_signals_fetched = len(all_signals)
        logger.info("Total signals fetched: %d", len(all_signals))

        # Phase 2: Normalize
        normalized = self.normalizer.normalize(all_signals)
        logger.info("Normalized: %d signals", len(normalized))

        # Phase 3: Deduplicate
        unique = self.dedup.process(normalized)
        result.total_signals_after_dedup = len(unique)
        logger.info("After dedup: %d signals", len(unique))

        # Phase 4: Entity resolution
        entity_map = self.entity_resolver.resolve_batch(unique)
        result.entity_map = entity_map
        result.total_entity_matches = sum(len(m) for m in entity_map.values())
        logger.info("Entity matches: %d", result.total_entity_matches)

        # Store results
        result.signals = unique
        result.completed_at = datetime.utcnow()
        result.duration_seconds = round(time.monotonic() - start, 3)

        logger.info(
            "=== ETL Pipeline complete: %d signals in %.1fs ===",
            len(unique), result.duration_seconds,
        )
        return result

    async def run_source(self, source_name: str) -> PipelineResult:
        return await self.run(sources=[source_name])


async def main() -> None:
    pipeline = ETLPipeline()
    result = await pipeline.run()
    print(f"\nPipeline Results:")
    print(f"  Signals fetched:    {result.total_signals_fetched}")
    print(f"  After dedup:        {result.total_signals_after_dedup}")
    print(f"  Entity matches:     {result.total_entity_matches}")
    print(f"  Duration:           {result.duration_seconds}s")
    print(f"  Errors:             {len(result.errors)}")
    for err in result.errors:
        print(f"    - {err}")


if __name__ == "__main__":
    asyncio.run(main())
