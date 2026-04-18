"""Alert generator — creates actionable alerts from signals, scores, and anomalies."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from disney_dashboard.analytics.trends import TrendDetector, TrendDirection, TrendResult
from disney_dashboard.models.schemas import (
    Alert,
    AlertType,
    MetricSnapshot,
    MetricType,
    SentimentScore,
    Severity,
    Signal,
    SourceType,
)
from disney_dashboard.utils.logging import get_logger

logger = get_logger("alerts")


class AlertGenerator:
    def __init__(self) -> None:
        self.trend_detector = TrendDetector()

    def generate_all(
        self,
        entity_id: UUID,
        signals: List[Signal],
        sentiment_scores: List[SentimentScore],
        metrics: List[MetricSnapshot],
    ) -> List[Alert]:
        alerts: List[Alert] = []

        alerts.extend(self._check_sentiment_spikes(entity_id, sentiment_scores))
        alerts.extend(self._check_volume_anomalies(entity_id, signals))
        alerts.extend(self._check_filing_alerts(entity_id, signals))
        alerts.extend(self._check_competitor_moves(entity_id, signals))
        alerts.extend(self._check_trend_reversals(entity_id, sentiment_scores, metrics))

        logger.info("Generated %d alerts for entity %s", len(alerts), entity_id)
        return alerts

    def _check_sentiment_spikes(
        self, entity_id: UUID, scores: List[SentimentScore]
    ) -> List[Alert]:
        alerts: List[Alert] = []
        if len(scores) < 5:
            return alerts

        sorted_scores = sorted(scores, key=lambda s: s.scored_at)
        now = datetime.utcnow()
        cutoff_24h = now - timedelta(hours=24)
        cutoff_48h = now - timedelta(hours=48)

        recent = [s for s in sorted_scores if s.scored_at >= cutoff_24h]
        baseline = [s for s in sorted_scores if cutoff_48h <= s.scored_at < cutoff_24h]

        if not recent or not baseline:
            return alerts

        recent_avg = sum(s.polarity for s in recent) / len(recent)
        baseline_avg = sum(s.polarity for s in baseline) / len(baseline)
        delta = recent_avg - baseline_avg

        if delta < -0.30:
            alerts.append(Alert(
                entity_id=entity_id,
                alert_type=AlertType.SENTIMENT_SPIKE,
                severity=Severity.CRITICAL,
                headline=f"Critical sentiment drop: {delta:+.2f} in 24h",
                summary=(
                    f"Sentiment dropped from {baseline_avg:+.2f} to {recent_avg:+.2f} "
                    f"({len(recent)} recent signals). Immediate attention required."
                ),
                expires_at=now + timedelta(hours=48),
            ))
        elif delta < -0.15:
            alerts.append(Alert(
                entity_id=entity_id,
                alert_type=AlertType.SENTIMENT_SPIKE,
                severity=Severity.WARNING,
                headline=f"Sentiment decline: {delta:+.2f} in 24h",
                summary=(
                    f"Sentiment shifted from {baseline_avg:+.2f} to {recent_avg:+.2f}. "
                    f"Monitor for further deterioration."
                ),
                expires_at=now + timedelta(hours=24),
            ))
        elif delta > 0.25:
            alerts.append(Alert(
                entity_id=entity_id,
                alert_type=AlertType.SENTIMENT_SPIKE,
                severity=Severity.INFO,
                headline=f"Positive sentiment surge: {delta:+.2f} in 24h",
                summary=(
                    f"Sentiment improved from {baseline_avg:+.2f} to {recent_avg:+.2f}. "
                    f"Consider amplifying positive messaging."
                ),
                expires_at=now + timedelta(hours=24),
            ))

        return alerts

    def _check_volume_anomalies(
        self, entity_id: UUID, signals: List[Signal]
    ) -> List[Alert]:
        alerts: List[Alert] = []
        if len(signals) < 14:
            return alerts

        now = datetime.utcnow()
        daily_counts: dict[str, int] = {}
        for sig in signals:
            day_key = sig.ingested_at.strftime("%Y-%m-%d")
            daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

        if len(daily_counts) < 7:
            return alerts

        sorted_days = sorted(daily_counts.items())
        periods = [(datetime.strptime(d, "%Y-%m-%d"), c) for d, c in sorted_days]

        anomaly = self.trend_detector.detect_volume_anomaly(periods)
        if anomaly:
            severity = Severity.WARNING
            if anomaly.momentum > 3.0:
                severity = Severity.CRITICAL

            alerts.append(Alert(
                entity_id=entity_id,
                alert_type=AlertType.VOLUME_ANOMALY,
                severity=severity,
                headline=f"Signal volume spike: {anomaly.delta_pct:+.0f}% above average",
                summary=anomaly.description,
                expires_at=now + timedelta(hours=12),
            ))

        return alerts

    def _check_filing_alerts(
        self, entity_id: UUID, signals: List[Signal]
    ) -> List[Alert]:
        alerts: List[Alert] = []
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=24)

        filing_signals = [
            s for s in signals
            if s.source_type == SourceType.SEC_FILING and s.ingested_at >= cutoff
        ]

        for sig in filing_signals:
            form_type = sig.raw_payload.get("form_type", "")

            if form_type == "8-K":
                severity = Severity.CRITICAL
            elif form_type in ("10-K", "10-Q"):
                severity = Severity.WARNING
            else:
                severity = Severity.INFO

            alerts.append(Alert(
                signal_id=sig.id,
                entity_id=entity_id,
                alert_type=AlertType.FILING_DETECTED,
                severity=severity,
                headline=f"SEC {form_type} filing detected",
                summary=sig.body[:500],
                expires_at=now + timedelta(days=7),
            ))

        return alerts

    def _check_competitor_moves(
        self, entity_id: UUID, signals: List[Signal]
    ) -> List[Alert]:
        alerts: List[Alert] = []
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=24)

        competitor_signals = [
            s for s in signals
            if s.source_type == SourceType.COMPETITOR and s.ingested_at >= cutoff
        ]

        competitor_keywords = [
            "opening", "announcement", "expansion", "new ride",
            "price cut", "acquisition", "partnership",
        ]

        for sig in competitor_signals:
            text = f"{sig.title} {sig.body}".lower()
            matches = [kw for kw in competitor_keywords if kw in text]
            if matches:
                alerts.append(Alert(
                    signal_id=sig.id,
                    entity_id=entity_id,
                    alert_type=AlertType.COMPETITOR_MOVE,
                    severity=Severity.WARNING,
                    headline=f"Competitor activity: {sig.title[:120]}",
                    summary=f"Detected keywords: {', '.join(matches)}. {sig.body[:300]}",
                    expires_at=now + timedelta(days=3),
                ))

        return alerts

    def _check_trend_reversals(
        self,
        entity_id: UUID,
        sentiment_scores: List[SentimentScore],
        metrics: List[MetricSnapshot],
    ) -> List[Alert]:
        alerts: List[Alert] = []
        now = datetime.utcnow()

        sentiment_trend = self.trend_detector.detect_sentiment_trend(sentiment_scores)
        if sentiment_trend.direction == TrendDirection.REVERSING:
            alerts.append(Alert(
                entity_id=entity_id,
                alert_type=AlertType.TREND_REVERSAL,
                severity=Severity.WARNING,
                headline="Sentiment trend reversal detected",
                summary=sentiment_trend.description,
                expires_at=now + timedelta(hours=24),
            ))

        metric_groups: dict[MetricType, List[MetricSnapshot]] = {}
        for m in metrics:
            metric_groups.setdefault(m.metric_type, []).append(m)

        for metric_type, snapshots in metric_groups.items():
            trend = self.trend_detector.detect_metric_trend(
                metric_type.value, snapshots
            )
            if trend.direction == TrendDirection.REVERSING:
                alerts.append(Alert(
                    entity_id=entity_id,
                    alert_type=AlertType.TREND_REVERSAL,
                    severity=Severity.WARNING,
                    headline=f"Trend reversal: {metric_type.value}",
                    summary=trend.description,
                    expires_at=now + timedelta(hours=48),
                ))

        return alerts
