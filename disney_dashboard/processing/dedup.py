"""Deduplication engine — prevents duplicate signals using exact and fuzzy matching."""

from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from typing import Dict, List, Set

from disney_dashboard.models.schemas import Signal
from disney_dashboard.utils.logging import get_logger

logger = get_logger("dedup")


class DeduplicationEngine:
    def __init__(self, similarity_threshold: float = 0.85) -> None:
        self.similarity_threshold = similarity_threshold
        self._hash_index: Set[str] = set()
        self._title_index: Dict[str, str] = {}

    def process(self, signals: List[Signal]) -> List[Signal]:
        unique: List[Signal] = []
        duplicates = 0

        for signal in signals:
            exact_hash = self._exact_hash(signal)
            if exact_hash in self._hash_index:
                duplicates += 1
                continue

            if self._is_fuzzy_duplicate(signal):
                duplicates += 1
                continue

            self._hash_index.add(exact_hash)
            normalized_title = self._normalize_title(signal.title)
            self._title_index[normalized_title] = str(signal.id)
            signal.dedup_hash = exact_hash
            unique.append(signal)

        logger.info(
            "Dedup: %d input → %d unique, %d duplicates removed",
            len(signals), len(unique), duplicates,
        )
        return unique

    def _exact_hash(self, signal: Signal) -> str:
        key = f"{signal.source_type.value}:{signal.source_url or signal.title}"
        return hashlib.sha256(key.lower().encode()).hexdigest()

    def _is_fuzzy_duplicate(self, signal: Signal) -> bool:
        normalized = self._normalize_title(signal.title)
        if not normalized:
            return False

        for existing_title in self._title_index:
            ratio = SequenceMatcher(None, normalized, existing_title).ratio()
            if ratio >= self.similarity_threshold:
                return True
        return False

    @staticmethod
    def _normalize_title(title: str) -> str:
        title = title.lower().strip()
        title = re.sub(r"[^\w\s]", "", title)
        title = re.sub(r"\s+", " ", title)
        return title

    def reset(self) -> None:
        self._hash_index.clear()
        self._title_index.clear()
