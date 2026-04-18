"""Health scoring engine — computes 0-100 scores per entity using weighted components."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from disney_dashboard.models.schemas import (
    MetricSnapshot,
    MetricType,
    Period,
    Scorecard,
    SentimentScore,
    Signal,
)
from disney_dashboard.utils.logging import get_logger

logger = get_logger("scoring")


COMPONENT_WEIGHTS = {
    "sentiment": 0.30,
    "volume": 0.15,
    "financial": 0.25,
    "operational": 0.20,
    "competitive": 0.10,
}


@dataclass
class ComponentScore:
    name: str
    value: float  # 0-100
    weight: float
    contributing_factors: List[str] = field(default_factory=list)


@dataclass
class HealthScoreResult:
    entity_name: str
    overall_score: float
    components: Dict[str, ComponentScore] = field(default_factory=dict)
    risk_flags: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    computed_at: datetime = field(default_factory=datetime.utcnow)


class HealthScoringEngine:
    def compute_health_score(
        self,
        entity_name: str,
        sentiment_scores: List[SentimentScore],
        signals: List[Signal],
        metrics: List[MetricSnapshot],
        competitor_metrics: Optional[List[MetricSnapshot]] = None,
    ) -> HealthScoreResult:
        result = HealthScoreResult(entity_name=entity_name)

        sentiment_comp = self._score_sentiment(sentiment_scores)
        result.components["sentiment"] = sentiment_comp

        volume_comp = self._score_volume(signals)
        result.components["volume"] = volume_comp

        financial_comp = self._score_financial(metrics)
        result.components["financial"] = financial_comp

        operational_comp = self._score_operational(metrics)
        result.components["operational"] = operational_comp

        competitive_comp = self._score_competitive(
            sentiment_scores, signals, competitor_metrics or []
        )
        result.components["competitive"] = competitive_comp

        result.overall_score = round(
            sum(c.value * c.weight for c in result.components.values()), 1
        )

        result.risk_flags = self._identify_risks(result)
        result.opportunities = self._identify_opportunities(result)

        logger.info(
            "Health score for %s: %.1f (sentiment=%.0f, volume=%.0f, "
            "financial=%.0f, ops=%.0f, competitive=%.0f)",
            entity_name,
            result.overall_score,
            sentiment_comp.value,
            volume_comp.value,
            financial_comp.value,
            operational_comp.value,
            competitive_comp.value,
        )
        return result

    def _score_sentiment(self, scores: List[SentimentScore]) -> ComponentScore:
        comp = ComponentScore(name="sentiment", value=50.0, weight=COMPONENT_WEIGHTS["sentiment"])

        if not scores:
            comp.contributing_factors.append("No sentiment data available")
            return comp

        polarities = [s.polarity for s in scores]
        avg_polarity = sum(polarities) / len(polarities)
        normalized = (avg_polarity + 1) / 2 * 100  # [-1,1] → [0,100]

        confidences = [s.confidence for s in scores]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        normalized *= (0.5 + avg_confidence * 0.5)
        normalized = max(0, min(100, normalized))

        now = datetime.utcnow()
        recent_cutoff = now - timedelta(hours=24)
        recent = [s for s in scores if s.scored_at >= recent_cutoff]
        older = [s for s in scores if s.scored_at < recent_cutoff]

        if recent and older:
            recent_avg = sum(s.polarity for s in recent) / len(recent)
            older_avg = sum(s.polarity for s in older) / len(older)
            delta = recent_avg - older_avg

            if delta < -0.15:
                normalized *= 0.85
                comp.contributing_factors.append(
                    f"Sharp negative swing: {delta:+.2f} in 24h"
                )
            elif delta > 0.15:
                normalized = min(100, normalized * 1.1)
                comp.contributing_factors.append(
                    f"Strong positive momentum: {delta:+.2f} in 24h"
                )

        comp.value = round(normalized, 1)
        comp.contributing_factors.append(f"Avg polarity: {avg_polarity:+.3f}")
        comp.contributing_factors.append(f"Sample size: {len(scores)}")
        return comp

    def _score_volume(self, signals: List[Signal]) -> ComponentScore:
        comp = ComponentScore(name="volume", value=50.0, weight=COMPONENT_WEIGHTS["volume"])

        if not signals:
            comp.contributing_factors.append("No signal volume data")
            return comp

        now = datetime.utcnow()
        last_24h = [s for s in signals if s.ingested_at >= now - timedelta(hours=24)]
        last_7d = [s for s in signals if s.ingested_at >= now - timedelta(days=7)]

        daily_rate = len(last_24h)
        weekly_avg_daily = len(last_7d) / 7 if last_7d else 1

        if weekly_avg_daily == 0:
            weekly_avg_daily = 1

        volume_ratio = daily_rate / weekly_avg_daily

        if volume_ratio > 3.0:
            score = 85
            comp.contributing_factors.append(f"Volume spike: {volume_ratio:.1f}x average")
        elif volume_ratio > 1.5:
            score = 70
            comp.contributing_factors.append(f"Above-average buzz: {volume_ratio:.1f}x")
        elif volume_ratio > 0.7:
            score = 55
            comp.contributing_factors.append("Normal volume")
        elif volume_ratio > 0.3:
            score = 35
            comp.contributing_factors.append(f"Below-average volume: {volume_ratio:.1f}x")
        else:
            score = 20
            comp.contributing_factors.append("Very low signal volume — staleness risk")

        comp.value = float(score)
        comp.contributing_factors.append(f"24h signals: {daily_rate}")
        return comp

    def _score_financial(self, metrics: List[MetricSnapshot]) -> ComponentScore:
        comp = ComponentScore(name="financial", value=50.0, weight=COMPONENT_WEIGHTS["financial"])

        financial_types = {
            MetricType.REVENUE_EXPERIENCES,
            MetricType.OPERATING_INCOME,
            MetricType.PER_CAPITA_GUEST_SPENDING,
            MetricType.ANALYST_RATING_AVG,
        }
        financial_metrics = [m for m in metrics if m.metric_type in financial_types]

        if not financial_metrics:
            comp.contributing_factors.append("No financial metrics available")
            return comp

        scores_list: List[float] = []

        revenue = [m for m in financial_metrics if m.metric_type == MetricType.REVENUE_EXPERIENCES]
        if revenue:
            latest = max(revenue, key=lambda m: m.period_end)
            if latest.delta_pct is not None:
                rev_score = 50 + latest.delta_pct * 5
                rev_score = max(0, min(100, rev_score))
                scores_list.append(rev_score)
                comp.contributing_factors.append(
                    f"Revenue delta: {latest.delta_pct:+.1f}%"
                )

        analyst = [m for m in financial_metrics if m.metric_type == MetricType.ANALYST_RATING_AVG]
        if analyst:
            latest = max(analyst, key=lambda m: m.period_end)
            rating_score = (latest.value / 5.0) * 100
            scores_list.append(rating_score)
            comp.contributing_factors.append(f"Analyst rating: {latest.value:.1f}/5.0")

        spending = [m for m in financial_metrics if m.metric_type == MetricType.PER_CAPITA_GUEST_SPENDING]
        if spending:
            latest = max(spending, key=lambda m: m.period_end)
            if latest.delta_pct is not None:
                spend_score = 50 + latest.delta_pct * 3
                spend_score = max(0, min(100, spend_score))
                scores_list.append(spend_score)
                comp.contributing_factors.append(
                    f"Per-capita spend delta: {latest.delta_pct:+.1f}%"
                )

        if scores_list:
            comp.value = round(sum(scores_list) / len(scores_list), 1)

        return comp

    def _score_operational(self, metrics: List[MetricSnapshot]) -> ComponentScore:
        comp = ComponentScore(name="operational", value=50.0, weight=COMPONENT_WEIGHTS["operational"])

        ops_types = {
            MetricType.PARK_WAIT_TIME_AVG,
            MetricType.PARK_WAIT_TIME_P90,
            MetricType.PARK_CROWD_LEVEL,
            MetricType.PARK_HOURS_TOTAL,
        }
        ops_metrics = [m for m in metrics if m.metric_type in ops_types]

        if not ops_metrics:
            comp.contributing_factors.append("No operational metrics available")
            return comp

        scores_list: List[float] = []

        wait_avg = [m for m in ops_metrics if m.metric_type == MetricType.PARK_WAIT_TIME_AVG]
        if wait_avg:
            latest = max(wait_avg, key=lambda m: m.period_end)
            # Lower waits = better experience; 0 min → 100, 90+ min → 20
            wait_score = max(20, 100 - (latest.value * 0.9))
            scores_list.append(wait_score)
            comp.contributing_factors.append(f"Avg wait: {latest.value:.0f} min")

        crowd = [m for m in ops_metrics if m.metric_type == MetricType.PARK_CROWD_LEVEL]
        if crowd:
            latest = max(crowd, key=lambda m: m.period_end)
            level = latest.value
            # Moderate crowds (4-6) are optimal (good revenue, okay experience)
            if 4 <= level <= 6:
                crowd_score = 80
            elif 3 <= level <= 7:
                crowd_score = 65
            elif level <= 2:
                crowd_score = 40  # Too empty = revenue concern
            else:
                crowd_score = 30  # Too packed = experience concern
            scores_list.append(crowd_score)
            comp.contributing_factors.append(f"Crowd level: {level:.0f}/10")

        hours = [m for m in ops_metrics if m.metric_type == MetricType.PARK_HOURS_TOTAL]
        if hours:
            latest = max(hours, key=lambda m: m.period_end)
            # More park hours = more capacity/revenue; 14+ hours = great
            hours_score = min(100, latest.value * 6.5)
            scores_list.append(hours_score)
            comp.contributing_factors.append(f"Park hours: {latest.value:.0f}h")

        if scores_list:
            comp.value = round(sum(scores_list) / len(scores_list), 1)

        return comp

    def _score_competitive(
        self,
        sentiment_scores: List[SentimentScore],
        signals: List[Signal],
        competitor_metrics: List[MetricSnapshot],
    ) -> ComponentScore:
        comp = ComponentScore(
            name="competitive", value=50.0, weight=COMPONENT_WEIGHTS["competitive"]
        )

        scores_list: List[float] = []

        sov_metrics = [
            m for m in competitor_metrics
            if m.metric_type == MetricType.SHARE_OF_VOICE
        ]
        if sov_metrics:
            latest = max(sov_metrics, key=lambda m: m.period_end)
            sov_score = min(100, latest.value * 2)
            scores_list.append(sov_score)
            comp.contributing_factors.append(
                f"Share of voice: {latest.value:.0f}%"
            )

        gap_metrics = [
            m for m in competitor_metrics
            if m.metric_type == MetricType.COMPETITOR_SENTIMENT_GAP
        ]
        if gap_metrics:
            latest = max(gap_metrics, key=lambda m: m.period_end)
            # Positive gap = Disney sentiment is higher than competitors
            gap_score = 50 + latest.value * 50
            gap_score = max(0, min(100, gap_score))
            scores_list.append(gap_score)
            comp.contributing_factors.append(
                f"Sentiment gap vs competitors: {latest.value:+.2f}"
            )

        if not scores_list and sentiment_scores:
            avg_polarity = sum(s.polarity for s in sentiment_scores) / len(sentiment_scores)
            base_score = (avg_polarity + 1) / 2 * 100
            scores_list.append(base_score)
            comp.contributing_factors.append("Estimated from own sentiment (no competitor data)")

        if scores_list:
            comp.value = round(sum(scores_list) / len(scores_list), 1)

        return comp

    @staticmethod
    def _identify_risks(result: HealthScoreResult) -> List[str]:
        risks: List[str] = []

        sentiment = result.components.get("sentiment")
        if sentiment and sentiment.value < 35:
            risks.append("Sentiment below critical threshold")

        volume = result.components.get("volume")
        if volume:
            for factor in volume.contributing_factors:
                if "spike" in factor.lower():
                    if sentiment and sentiment.value < 45:
                        risks.append("Volume spike combined with negative sentiment")

        ops = result.components.get("operational")
        if ops and ops.value < 30:
            risks.append("Operational stress — high wait times or crowd levels")

        financial = result.components.get("financial")
        if financial and financial.value < 40:
            risks.append("Financial metrics trending below expectations")

        if result.overall_score < 40:
            risks.append("Overall health score in warning zone")

        return risks

    @staticmethod
    def _identify_opportunities(result: HealthScoreResult) -> List[str]:
        opportunities: List[str] = []

        sentiment = result.components.get("sentiment")
        if sentiment and sentiment.value > 75:
            opportunities.append("Strong positive sentiment — capitalize on brand momentum")

        volume = result.components.get("volume")
        if volume and volume.value > 70:
            opportunities.append("High engagement — amplify key messages")

        competitive = result.components.get("competitive")
        if competitive and competitive.value > 70:
            opportunities.append("Competitive advantage — widen the gap")

        ops = result.components.get("operational")
        if ops and ops.value > 75:
            opportunities.append("Operational excellence — guest experience is strong")

        return opportunities

    def generate_scorecard(
        self,
        entity_id,
        health_result: HealthScoreResult,
        signals: List[Signal],
        sentiment_scores: List[SentimentScore],
        period: Period = Period.DAILY,
    ) -> Scorecard:
        avg_sentiment = 0.0
        if sentiment_scores:
            avg_sentiment = sum(s.polarity for s in sentiment_scores) / len(sentiment_scores)

        return Scorecard(
            entity_id=entity_id,
            period=period,
            period_date=datetime.utcnow(),
            overall_score=health_result.overall_score,
            sentiment_avg=round(avg_sentiment, 4),
            signal_volume=len(signals),
            risk_flags=health_result.risk_flags,
            opportunities=health_result.opportunities,
        )
