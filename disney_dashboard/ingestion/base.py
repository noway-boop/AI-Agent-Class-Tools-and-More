"""Base ingestion connector with retry, rate limiting, and deduplication."""

from __future__ import annotations

import asyncio
import hashlib
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Set

import aiohttp

from disney_dashboard.models.schemas import (
    IngestionResult,
    Signal,
    SourceType,
)
from disney_dashboard.utils.logging import get_logger
from disney_dashboard.utils.rate_limiter import RateLimiter


class BaseConnector(ABC):
    source_type: SourceType
    source_name: str

    def __init__(
        self,
        rate_limit: float = 1.0,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        timeout: int = 30,
    ) -> None:
        self.rate_limiter = RateLimiter(calls_per_second=rate_limit)
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.timeout = timeout
        self.logger = get_logger(self.source_name)
        self._seen_hashes: Set[str] = set()

    @abstractmethod
    async def fetch(self) -> List[Signal]:
        ...

    async def run(self) -> IngestionResult:
        result = IngestionResult(
            source_type=self.source_type,
            source_name=self.source_name,
        )
        start = time.monotonic()
        try:
            signals = await self.fetch()
            result.signals_fetched = len(signals)
            unique: List[Signal] = []
            for signal in signals:
                h = self._compute_hash(signal)
                signal.dedup_hash = h
                if h not in self._seen_hashes:
                    self._seen_hashes.add(h)
                    unique.append(signal)
                else:
                    result.signals_duplicate += 1
            result.signals_new = len(unique)
            self.logger.info(
                "Fetched %d signals (%d new, %d duplicate)",
                result.signals_fetched,
                result.signals_new,
                result.signals_duplicate,
            )
        except Exception as exc:
            result.errors.append(str(exc))
            self.logger.error("Ingestion failed: %s", exc)
        finally:
            result.completed_at = datetime.utcnow()
            result.duration_seconds = round(time.monotonic() - start, 3)
        return result

    async def _request(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        json_body: Optional[dict] = None,
    ) -> dict:
        await self.rate_limiter.acquire()
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        headers=headers,
                        params=params,
                        json=json_body,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as resp:
                        resp.raise_for_status()
                        return await resp.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_exc = exc
                wait = self.retry_backoff ** attempt
                self.logger.warning(
                    "Request to %s failed (attempt %d/%d): %s — retrying in %.1fs",
                    url, attempt, self.max_retries, exc, wait,
                )
                await asyncio.sleep(wait)

        raise ConnectionError(
            f"Failed after {self.max_retries} retries: {last_exc}"
        )

    async def _request_text(
        self,
        url: str,
        *,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> str:
        await self.rate_limiter.acquire()
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        "GET",
                        url,
                        headers=headers,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as resp:
                        resp.raise_for_status()
                        return await resp.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_exc = exc
                wait = self.retry_backoff ** attempt
                self.logger.warning(
                    "Text request to %s failed (attempt %d/%d): %s",
                    url, attempt, self.max_retries, exc,
                )
                await asyncio.sleep(wait)

        raise ConnectionError(
            f"Failed after {self.max_retries} retries: {last_exc}"
        )

    @staticmethod
    def _compute_hash(signal: Signal) -> str:
        normalized = f"{signal.source_type.value}:{signal.title.lower().strip()}"
        return hashlib.sha256(normalized.encode()).hexdigest()
