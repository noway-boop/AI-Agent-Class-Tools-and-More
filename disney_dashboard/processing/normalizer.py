"""Signal normalizer — cleans and standardizes raw signal data."""

from __future__ import annotations

import html
import re
from typing import List

from disney_dashboard.models.schemas import Signal
from disney_dashboard.utils.logging import get_logger

logger = get_logger("normalizer")


class SignalNormalizer:
    MAX_TITLE_LENGTH = 500
    MAX_BODY_LENGTH = 5000

    def normalize(self, signals: List[Signal]) -> List[Signal]:
        normalized: List[Signal] = []
        for signal in signals:
            try:
                normalized.append(self._normalize_signal(signal))
            except Exception as exc:
                logger.warning(
                    "Failed to normalize signal %s: %s", signal.id, exc
                )
        logger.info("Normalized %d/%d signals", len(normalized), len(signals))
        return normalized

    def _normalize_signal(self, signal: Signal) -> Signal:
        signal.title = self._clean_text(signal.title)[: self.MAX_TITLE_LENGTH]
        signal.body = self._clean_text(signal.body)[: self.MAX_BODY_LENGTH]

        if not signal.title and signal.body:
            signal.title = signal.body[:200]

        return signal

    @staticmethod
    def _clean_text(text: str) -> str:
        if not text:
            return ""
        text = html.unescape(text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text
