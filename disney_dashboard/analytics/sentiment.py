"""Sentiment analyzer — scores signals using VADER and optional Claude API."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from disney_dashboard.models.schemas import SentimentScore, Signal, Urgency
from disney_dashboard.utils.logging import get_logger

logger = get_logger("sentiment")


class SentimentAnalyzer:
    def __init__(self, anthropic_api_key: str = "") -> None:
        self.anthropic_api_key = anthropic_api_key
        self._vader = None

    def _get_vader(self):
        if self._vader is None:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self._vader = SentimentIntensityAnalyzer()
        return self._vader

    def analyze_vader(self, signal: Signal) -> SentimentScore:
        vader = self._get_vader()
        text = f"{signal.title}. {signal.body}" if signal.body else signal.title
        text = text[:5000]

        scores = vader.polarity_scores(text)
        compound = scores["compound"]
        pos = scores["pos"]
        neg = scores["neg"]

        magnitude = max(pos, neg)
        confidence = abs(compound) * 0.7 + magnitude * 0.3

        return SentimentScore(
            signal_id=signal.id,
            model_used="vader",
            polarity=round(compound, 4),
            magnitude=round(magnitude, 4),
            urgency=self._classify_urgency_from_sentiment(compound, magnitude),
            confidence=round(min(1.0, confidence), 4),
            scored_at=datetime.utcnow(),
        )

    def analyze_batch_vader(self, signals: List[Signal]) -> List[SentimentScore]:
        results = []
        for signal in signals:
            try:
                score = self.analyze_vader(signal)
                results.append(score)
            except Exception as exc:
                logger.warning("VADER scoring failed for %s: %s", signal.id, exc)
        logger.info("VADER scored %d/%d signals", len(results), len(signals))
        return results

    async def analyze_claude(self, signal: Signal) -> Optional[SentimentScore]:
        if not self.anthropic_api_key:
            return None

        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
            text = f"{signal.title}. {signal.body}" if signal.body else signal.title
            text = text[:3000]

            prompt = (
                "Analyze the sentiment of this text about Disney theme parks / experiences. "
                "Return ONLY a JSON object with these fields:\n"
                '- "polarity": float from -1.0 (very negative) to 1.0 (very positive)\n'
                '- "magnitude": float from 0.0 (neutral/weak) to 1.0 (strong opinion)\n'
                '- "urgency": one of "low", "medium", "high", "critical"\n'
                '- "confidence": float from 0.0 to 1.0\n'
                '- "summary": one-sentence summary of sentiment driver\n\n'
                f"Text:\n{text}"
            )

            message = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )

            import json
            response_text = message.content[0].text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0]
            parsed = json.loads(response_text)

            urgency_map = {
                "low": Urgency.LOW,
                "medium": Urgency.MEDIUM,
                "high": Urgency.HIGH,
                "critical": Urgency.CRITICAL,
            }

            return SentimentScore(
                signal_id=signal.id,
                model_used="claude",
                polarity=round(float(parsed.get("polarity", 0)), 4),
                magnitude=round(float(parsed.get("magnitude", 0)), 4),
                urgency=urgency_map.get(parsed.get("urgency", "low"), Urgency.LOW),
                confidence=round(float(parsed.get("confidence", 0.8)), 4),
                scored_at=datetime.utcnow(),
            )
        except Exception as exc:
            logger.warning("Claude sentiment failed for %s: %s", signal.id, exc)
            return None

    async def analyze_batch_claude(
        self, signals: List[Signal], max_concurrent: int = 5
    ) -> List[SentimentScore]:
        if not self.anthropic_api_key:
            logger.info("No Anthropic API key — skipping Claude sentiment")
            return []

        semaphore = asyncio.Semaphore(max_concurrent)
        results: List[SentimentScore] = []

        async def _analyze_one(sig: Signal) -> None:
            async with semaphore:
                score = await self.analyze_claude(sig)
                if score:
                    results.append(score)

        await asyncio.gather(*[_analyze_one(s) for s in signals])
        logger.info("Claude scored %d/%d signals", len(results), len(signals))
        return results

    def merge_scores(
        self, vader_scores: List[SentimentScore], claude_scores: List[SentimentScore]
    ) -> Dict[str, SentimentScore]:
        score_map: Dict[str, SentimentScore] = {}

        for score in vader_scores:
            score_map[str(score.signal_id)] = score

        for score in claude_scores:
            sid = str(score.signal_id)
            if sid in score_map:
                vader = score_map[sid]
                merged = SentimentScore(
                    signal_id=score.signal_id,
                    model_used="merged",
                    polarity=round(vader.polarity * 0.3 + score.polarity * 0.7, 4),
                    magnitude=round(vader.magnitude * 0.3 + score.magnitude * 0.7, 4),
                    urgency=score.urgency,
                    confidence=round(
                        vader.confidence * 0.3 + score.confidence * 0.7, 4
                    ),
                    scored_at=datetime.utcnow(),
                )
                score_map[sid] = merged
            else:
                score_map[sid] = score

        return score_map

    @staticmethod
    def _classify_urgency_from_sentiment(
        polarity: float, magnitude: float
    ) -> Urgency:
        if polarity < -0.6 and magnitude > 0.5:
            return Urgency.CRITICAL
        if polarity < -0.3 and magnitude > 0.3:
            return Urgency.HIGH
        if polarity < -0.1:
            return Urgency.MEDIUM
        return Urgency.LOW
