"""Trend detector — identifies direction, momentum, and reversals in time-series data."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from disney_dashboard.models.schemas import MetricSnapshot, SentimentScore
from disney_dashboard.utils.logging import get_logger

logger = get_logger("trends")


class TrendDirection(str, enum.Enum):
    ACCELERATING = "accelerating"
    STABLE = "stable"
    DECELERATING = "decelerating"
    REVERSING = "reversing"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class TrendResult:
    metric_name: str
    direction: TrendDirection
    short_term_avg: float
    long_term_avg: float
    delta_pct: float
    momentum: float  # rate of change
    data_points: int
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    description: str = ""


class TrendDetector:
    def __init__(
        self,
        short_window_days: int = 7,
        long_window_days: int = 30,
        acceleration_threshold: float = 0.10,
    ) -> None:
        self.short_window = timedelta(days=short_window_days)
        self.long_window = timedelta(days=long_window_days)
        self.threshold = acceleration_threshold

    def detect_metric_trend(
        self, metric_name: str, snapshots: List[MetricSnapshot]
    ) -> TrendResult:
        if len(snapshots) < 3:
            return TrendResult(
                metric_name=metric_name,
                direction=TrendDirection.INSUFFICIENT_DATA,
                short_term_avg=0,
                long_term_avg=0,
                delta_pct=0,
                momentum=0,
                data_points=len(snapshots),
                description="Not enough data points for trend analysis",
            )

        sorted_snaps = sorted(snapshots, key=lambda s: s.period_end)
        now = sorted_snaps[-1].period_end

        short_cutoff = now - self.short_window
        long_cutoff = now - self.long_window

        short_values = [s.value for s in sorted_snaps if s.period_end >= short_cutoff]
        long_values = [s.value for s in sorted_snaps if s.period_end >= long_cutoff]

        short_avg = sum(short_values) / len(short_values) if short_values else 0
        long_avg = sum(long_values) / len(long_values) if long_values else 0

        if long_avg == 0:
            delta_pct = 0.0
        else:
            delta_pct = (short_avg - long_avg) / abs(long_avg)

        momentum = self._compute_momentum(short_values)

        direction = self._classify_direction(delta_pct, short_values, long_values)

        description = self._describe_trend(metric_name, direction, delta_pct, momentum)

        return TrendResult(
            metric_name=metric_name,
            direction=direction,
            short_term_avg=round(short_avg, 4),
            long_term_avg=round(long_avg, 4),
            delta_pct=round(delta_pct * 100, 2),
            momentum=round(momentum, 4),
            data_points=len(sorted_snaps),
            period_start=sorted_snaps[0].period_end,
            period_end=now,
            description=description,
        )

    def detect_sentiment_trend(
        self, scores: List[SentimentScore]
    ) -> TrendResult:
        if len(scores) < 3:
            return TrendResult(
                metric_name="sentiment",
                direction=TrendDirection.INSUFFICIENT_DATA,
                short_term_avg=0,
                long_term_avg=0,
                delta_pct=0,
                momentum=0,
                data_points=len(scores),
                description="Not enough sentiment data for trend analysis",
            )

        sorted_scores = sorted(scores, key=lambda s: s.scored_at)
        now = sorted_scores[-1].scored_at

        short_cutoff = now - self.short_window
        long_cutoff = now - self.long_window

        short_vals = [s.polarity for s in sorted_scores if s.scored_at >= short_cutoff]
        long_vals = [s.polarity for s in sorted_scores if s.scored_at >= long_cutoff]

        short_avg = sum(short_vals) / len(short_vals) if short_vals else 0
        long_avg = sum(long_vals) / len(long_vals) if long_vals else 0

        delta = short_avg - long_avg
        momentum = self._compute_momentum(short_vals)

        direction = self._classify_direction(
            delta if long_avg == 0 else delta / max(abs(long_avg), 0.01),
            short_vals,
            long_vals,
        )

        return TrendResult(
            metric_name="sentiment",
            direction=direction,
            short_term_avg=round(short_avg, 4),
            long_term_avg=round(long_avg, 4),
            delta_pct=round(delta * 100, 2),
            momentum=round(momentum, 4),
            data_points=len(sorted_scores),
            period_start=sorted_scores[0].scored_at,
            period_end=now,
            description=self._describe_trend("Sentiment", direction, delta, momentum),
        )

    def detect_volume_anomaly(
        self,
        signals_per_period: List[Tuple[datetime, int]],
        std_multiplier: float = 2.0,
    ) -> Optional[TrendResult]:
        if len(signals_per_period) < 7:
            return None

        sorted_periods = sorted(signals_per_period, key=lambda x: x[0])
        values = [v for _, v in sorted_periods]

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = variance ** 0.5

        latest = values[-1]
        threshold = mean + std_multiplier * std

        if latest > threshold:
            anomaly_strength = (latest - mean) / std if std > 0 else 0
            return TrendResult(
                metric_name="signal_volume_anomaly",
                direction=TrendDirection.ACCELERATING,
                short_term_avg=float(latest),
                long_term_avg=round(mean, 2),
                delta_pct=round(((latest - mean) / mean) * 100, 2) if mean > 0 else 0,
                momentum=round(anomaly_strength, 2),
                data_points=len(values),
                period_start=sorted_periods[0][0],
                period_end=sorted_periods[-1][0],
                description=(
                    f"Volume anomaly detected: {latest} signals vs "
                    f"{mean:.0f} average ({anomaly_strength:.1f} std devs)"
                ),
            )
        return None

    def _classify_direction(
        self,
        delta_pct: float,
        short_values: List[float],
        long_values: List[float],
    ) -> TrendDirection:
        if delta_pct > self.threshold:
            return TrendDirection.ACCELERATING
        if delta_pct < -self.threshold:
            return TrendDirection.DECELERATING

        if short_values and long_values:
            short_sign = 1 if sum(short_values) / len(short_values) >= 0 else -1
            long_sign = 1 if sum(long_values) / len(long_values) >= 0 else -1
            if short_sign != long_sign:
                return TrendDirection.REVERSING

        return TrendDirection.STABLE

    @staticmethod
    def _compute_momentum(values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
        return sum(deltas) / len(deltas)

    @staticmethod
    def _describe_trend(
        name: str, direction: TrendDirection, delta: float, momentum: float
    ) -> str:
        descriptions = {
            TrendDirection.ACCELERATING: f"{name} is accelerating ({delta:+.1f}% vs baseline, momentum {momentum:+.3f})",
            TrendDirection.STABLE: f"{name} is stable (within normal range)",
            TrendDirection.DECELERATING: f"{name} is declining ({delta:+.1f}% vs baseline, momentum {momentum:+.3f})",
            TrendDirection.REVERSING: f"{name} is reversing direction — sign flip detected",
            TrendDirection.INSUFFICIENT_DATA: f"{name}: not enough data for trend analysis",
        }
        return descriptions.get(direction, f"{name}: unknown trend")
