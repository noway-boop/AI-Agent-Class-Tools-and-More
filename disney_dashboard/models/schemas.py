"""Pydantic models for all dashboard data structures."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SourceType(str, enum.Enum):
    NEWS = "news"
    SEC_FILING = "sec_filing"
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    DISNEY_BLOG = "disney_blog"
    PARK_API = "park_api"
    EARNINGS = "earnings"
    COMPETITOR = "competitor"


class SignalStatus(str, enum.Enum):
    RAW = "raw"
    PROCESSED = "processed"
    SCORED = "scored"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class Urgency(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, enum.Enum):
    SENTIMENT_SPIKE = "sentiment_spike"
    VOLUME_ANOMALY = "volume_anomaly"
    FILING_DETECTED = "filing_detected"
    COMPETITOR_MOVE = "competitor_move"
    EARNINGS_SURPRISE = "earnings_surprise"
    TREND_REVERSAL = "trend_reversal"


class Severity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Period(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class MetricType(str, enum.Enum):
    PARK_WAIT_TIME_AVG = "park_wait_time_avg"
    PARK_WAIT_TIME_P90 = "park_wait_time_p90"
    PARK_CROWD_LEVEL = "park_crowd_level"
    LIGHTNING_LANE_PRICE = "lightning_lane_price"
    PARK_HOURS_TOTAL = "park_hours_total"
    SENTIMENT_POLARITY_AVG = "sentiment_polarity_avg"
    SENTIMENT_VOLUME = "sentiment_volume"
    SENTIMENT_DELTA_24H = "sentiment_delta_24h"
    SOCIAL_BUZZ_INDEX = "social_buzz_index"
    INFLUENCER_SENTIMENT = "influencer_sentiment"
    REVENUE_EXPERIENCES = "revenue_experiences"
    OPERATING_INCOME = "operating_income"
    PER_CAPITA_GUEST_SPENDING = "per_capita_guest_spending"
    HOTEL_OCCUPANCY_RATE = "hotel_occupancy_rate"
    ANALYST_RATING_AVG = "analyst_rating_avg"
    COMPETITOR_SENTIMENT_GAP = "competitor_sentiment_gap"
    SHARE_OF_VOICE = "share_of_voice"
    COMPETITOR_PRICE_INDEX = "competitor_price_index"


class Signal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_type: SourceType
    source_name: str
    source_url: str = ""
    title: str
    body: str = ""
    published_at: datetime
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    language: str = "en"
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    dedup_hash: str = ""
    status: SignalStatus = SignalStatus.RAW


class SignalEntity(BaseModel):
    signal_id: UUID
    entity_id: UUID
    relevance_score: float = 1.0
    extracted_by: str = "rule_based"


class SentimentScore(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    signal_id: UUID
    model_used: str = "vader"
    polarity: float = 0.0
    magnitude: float = 0.0
    urgency: Urgency = Urgency.LOW
    confidence: float = 0.0
    scored_at: datetime = Field(default_factory=datetime.utcnow)


class Entity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    entity_type: str  # company, segment, business_unit, property, topic
    parent_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricSnapshot(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    entity_id: UUID
    metric_type: MetricType
    value: float
    previous_value: Optional[float] = None
    delta_pct: Optional[float] = None
    period_start: datetime
    period_end: datetime
    source: str = ""
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


class Scorecard(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    entity_id: UUID
    period: Period
    period_date: datetime
    overall_score: float = 0.0
    sentiment_avg: float = 0.0
    signal_volume: int = 0
    risk_flags: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    signal_id: Optional[UUID] = None
    entity_id: UUID
    alert_type: AlertType
    severity: Severity = Severity.INFO
    headline: str
    summary: str = ""
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class IngestionResult(BaseModel):
    source_type: SourceType
    source_name: str
    signals_fetched: int = 0
    signals_new: int = 0
    signals_duplicate: int = 0
    errors: List[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
