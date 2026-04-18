"""Analytics aggregator — coordinates scoring, trends, and alerts into executive summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from disney_dashboard.analytics.alerts import AlertGenerator
from disney_dashboard.analytics.scoring import HealthScoreResult, HealthScoringEngine
from disney_dashboard.analytics.sentiment import SentimentAnalyzer
from disney_dashboard.analytics.trends import TrendDetector, TrendResult
from disney_dashboard.models.schemas import (
    Alert,
    MetricSnapshot,
    Period,
    Scorecard,
    SentimentScore,
    Signal,
)
from disney_dashboard.utils.logging import get_logger

logger = get_logger("aggregator")


@dataclass
class EntityAnalytics:
    entity_id: UUID
    entity_name: str
    health_score: Optional[HealthScoreResult] = None
    scorecard: Optional[Scorecard] = None
    sentiment_trend: Optional[TrendResult] = None
    metric_trends: Dict[str, TrendResult] = field(default_factory=dict)
    alerts: List[Alert] = field(default_factory=list)
    signal_count: int = 0
    computed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DashboardSnapshot:
    entities: Dict[str, EntityAnalytics] = field(default_factory=dict)
    total_signals: int = 0
    total_alerts: int = 0
    critical_alerts: int = 0
    top_risks: List[str] = field(default_factory=list)
    top_opportunities: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


class AnalyticsAggregator:
    def __init__(self, anthropic_api_key: str = "") -> None:
        self.sentiment_analyzer = SentimentAnalyzer(anthropic_api_key)
        self.scoring_engine = HealthScoringEngine()
        self.trend_detector = TrendDetector()
        self.alert_generator = AlertGenerator()

    async def analyze_entity(
        self,
        entity_id: UUID,
        entity_name: str,
        signals: List[Signal],
        metrics: List[MetricSnapshot],
        competitor_metrics: Optional[List[MetricSnapshot]] = None,
        use_claude_sentiment: bool = False,
    ) -> EntityAnalytics:
        analytics = EntityAnalytics(
            entity_id=entity_id,
            entity_name=entity_name,
            signal_count=len(signals),
        )

        # Step 1: Sentiment analysis
        vader_scores = self.sentiment_analyzer.analyze_batch_vader(signals)

        if use_claude_sentiment:
            high_impact = [s for s in signals if _is_high_impact(s)][:20]
            claude_scores = await self.sentiment_analyzer.analyze_batch_claude(high_impact)
            score_map = self.sentiment_analyzer.merge_scores(vader_scores, claude_scores)
            all_scores = list(score_map.values())
        else:
            all_scores = vader_scores

        # Step 2: Health scoring
        analytics.health_score = self.scoring_engine.compute_health_score(
            entity_name=entity_name,
            sentiment_scores=all_scores,
            signals=signals,
            metrics=metrics,
            competitor_metrics=competitor_metrics,
        )

        # Step 3: Generate scorecard
        analytics.scorecard = self.scoring_engine.generate_scorecard(
            entity_id=entity_id,
            health_result=analytics.health_score,
            signals=signals,
            sentiment_scores=all_scores,
            period=Period.DAILY,
        )

        # Step 4: Trend detection
        analytics.sentiment_trend = self.trend_detector.detect_sentiment_trend(all_scores)

        metric_groups: Dict[str, List[MetricSnapshot]] = {}
        for m in metrics:
            metric_groups.setdefault(m.metric_type.value, []).append(m)

        for metric_name, snapshots in metric_groups.items():
            analytics.metric_trends[metric_name] = (
                self.trend_detector.detect_metric_trend(metric_name, snapshots)
            )

        # Step 5: Alert generation
        analytics.alerts = self.alert_generator.generate_all(
            entity_id=entity_id,
            signals=signals,
            sentiment_scores=all_scores,
            metrics=metrics,
        )

        logger.info(
            "Entity %s: score=%.1f, %d alerts, sentiment trend=%s",
            entity_name,
            analytics.health_score.overall_score,
            len(analytics.alerts),
            analytics.sentiment_trend.direction.value if analytics.sentiment_trend else "n/a",
        )

        return analytics

    async def generate_dashboard_snapshot(
        self,
        entities: Dict[str, Dict],
    ) -> DashboardSnapshot:
        """Generate a full dashboard snapshot across all entities.

        Args:
            entities: Dict mapping entity_name -> {
                "entity_id": UUID,
                "signals": List[Signal],
                "metrics": List[MetricSnapshot],
                "competitor_metrics": Optional[List[MetricSnapshot]],
            }
        """
        snapshot = DashboardSnapshot()

        for entity_name, data in entities.items():
            analytics = await self.analyze_entity(
                entity_id=data["entity_id"],
                entity_name=entity_name,
                signals=data.get("signals", []),
                metrics=data.get("metrics", []),
                competitor_metrics=data.get("competitor_metrics"),
            )
            snapshot.entities[entity_name] = analytics
            snapshot.total_signals += analytics.signal_count
            snapshot.total_alerts += len(analytics.alerts)
            snapshot.critical_alerts += sum(
                1 for a in analytics.alerts if a.severity.value == "critical"
            )

        all_risks: List[str] = []
        all_opportunities: List[str] = []
        for entity_analytics in snapshot.entities.values():
            if entity_analytics.health_score:
                for risk in entity_analytics.health_score.risk_flags:
                    all_risks.append(
                        f"[{entity_analytics.entity_name}] {risk}"
                    )
                for opp in entity_analytics.health_score.opportunities:
                    all_opportunities.append(
                        f"[{entity_analytics.entity_name}] {opp}"
                    )

        snapshot.top_risks = all_risks[:10]
        snapshot.top_opportunities = all_opportunities[:10]

        logger.info(
            "Dashboard snapshot: %d entities, %d signals, %d alerts (%d critical)",
            len(snapshot.entities),
            snapshot.total_signals,
            snapshot.total_alerts,
            snapshot.critical_alerts,
        )

        return snapshot

    def format_executive_summary(self, snapshot: DashboardSnapshot) -> str:
        lines = [
            "=" * 70,
            "  DISNEY EXPERIENCES — EXECUTIVE INTELLIGENCE SUMMARY",
            f"  Generated: {snapshot.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            "=" * 70,
            "",
            f"  Signals Analyzed:  {snapshot.total_signals}",
            f"  Active Alerts:     {snapshot.total_alerts} ({snapshot.critical_alerts} critical)",
            "",
        ]

        ranked = sorted(
            snapshot.entities.items(),
            key=lambda x: x[1].health_score.overall_score if x[1].health_score else 0,
            reverse=True,
        )

        lines.append("  ENTITY HEALTH SCORES")
        lines.append("  " + "-" * 50)
        for name, analytics in ranked:
            score = analytics.health_score.overall_score if analytics.health_score else 0
            bar_len = int(score / 5)
            bar = "\u2588" * bar_len + "\u2591" * (20 - bar_len)
            trend_icon = ""
            if analytics.sentiment_trend:
                trend_map = {
                    "accelerating": "\u2191",
                    "decelerating": "\u2193",
                    "reversing": "\u21c5",
                    "stable": "\u2192",
                }
                trend_icon = trend_map.get(analytics.sentiment_trend.direction.value, "")
            lines.append(f"  {name:<30} {bar} {score:5.1f} {trend_icon}")

        if snapshot.top_risks:
            lines.append("")
            lines.append("  RISK FLAGS")
            lines.append("  " + "-" * 50)
            for risk in snapshot.top_risks[:5]:
                lines.append(f"  \u26a0  {risk}")

        if snapshot.top_opportunities:
            lines.append("")
            lines.append("  OPPORTUNITIES")
            lines.append("  " + "-" * 50)
            for opp in snapshot.top_opportunities[:5]:
                lines.append(f"  \u2605  {opp}")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)


def _is_high_impact(signal: Signal) -> bool:
    high_impact_sources = {
        "sec_edgar", "newsapi", "disney_parks_blog",
    }
    if signal.source_name in high_impact_sources:
        return True

    payload = signal.raw_payload
    if payload.get("score", 0) > 100:
        return True
    if payload.get("num_comments", 0) > 50:
        return True
    if payload.get("like_count", 0) > 1000:
        return True
    if payload.get("author_followers", 0) > 50000:
        return True

    return False
