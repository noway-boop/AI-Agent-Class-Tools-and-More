"""Central configuration for the Disney Intelligence Dashboard."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class APIConfig:
    news_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "DisneyDashboard/0.1"
    youtube_api_key: str = ""
    twitter_bearer_token: str = ""
    anthropic_api_key: str = ""
    fmp_api_key: str = ""  # Financial Modeling Prep


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    name: str = "disney_dashboard"
    user: str = "dashboard"
    password: str = ""
    redis_url: str = "redis://localhost:6379/0"
    elasticsearch_url: str = "http://localhost:9200"


@dataclass(frozen=True)
class IngestionConfig:
    news_interval_minutes: int = 60
    sec_interval_minutes: int = 360
    reddit_interval_minutes: int = 120
    youtube_interval_minutes: int = 120
    twitter_interval_minutes: int = 30
    disney_blog_interval_minutes: int = 60
    wait_times_interval_minutes: int = 5
    competitor_interval_minutes: int = 240
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    request_timeout: int = 30
    batch_size: int = 100


DISNEY_ENTITIES: Dict[str, List[str]] = {
    "Walt Disney World": [
        "Magic Kingdom", "EPCOT", "Hollywood Studios",
        "Animal Kingdom", "Disney Springs", "Typhoon Lagoon",
        "Blizzard Beach",
    ],
    "Disneyland Resort": [
        "Disneyland Park", "Disney California Adventure",
        "Downtown Disney",
    ],
    "Disney Cruise Line": [
        "Disney Wish", "Disney Fantasy", "Disney Dream",
        "Disney Magic", "Disney Wonder", "Disney Treasure",
        "Disney Destiny",
    ],
    "Shanghai Disney Resort": ["Shanghai Disneyland"],
    "Hong Kong Disneyland Resort": ["Hong Kong Disneyland"],
    "Tokyo Disney Resort": ["Tokyo Disneyland", "Tokyo DisneySea"],
    "Aulani": ["Aulani, A Disney Resort & Spa"],
    "Disneyland Paris": ["Disneyland Park Paris", "Walt Disney Studios Park"],
}

COMPETITORS: List[str] = [
    "Universal Studios", "Universal Orlando", "Universal Epic Universe",
    "SeaWorld", "Six Flags", "Cedar Fair", "Merlin Entertainments",
    "Legoland", "Busch Gardens", "Comcast NBCUniversal",
]

TRACKED_SUBREDDITS: List[str] = [
    "WaltDisneyWorld", "Disneyland", "DisneyParks",
    "DisneyCruiseLine", "DisneyWorld", "DisneyVacation",
]

TRACKED_YOUTUBE_CHANNELS: Dict[str, str] = {
    "UCnpWedLQdHpZqhgTLdB9Yyg": "DFBGuide",
    "UCe-0RYaOEjqJOvGvzJUJGAw": "AllEars.net",
    "UC6vDP0bZkDNc689IrFMBoag": "TPMVids",
    "UCk2poS_J1ZRz2EO3gLRHKdA": "Provost Park Pass",
    "UCYyJUEtYv-ZW7BgjhP3UbTg": "ResortTV1",
}

NEWS_KEYWORDS: List[str] = [
    "Disney Parks", "Walt Disney World", "Disneyland",
    "Disney Cruise Line", "Disney Experiences", "Disney theme park",
    "Magic Kingdom", "EPCOT", "Hollywood Studios",
    "Disney earnings", "Disney attendance", "Disney ticket prices",
    "Lightning Lane", "Disney Genie", "Disney vacation",
    "Epic Universe", "Universal Orlando",
]

SEC_CIK: str = "1744489"  # The Walt Disney Company


def load_config() -> tuple[APIConfig, DatabaseConfig, IngestionConfig]:
    api = APIConfig(
        news_api_key=os.getenv("NEWS_API_KEY", ""),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "DisneyDashboard/0.1"),
        youtube_api_key=os.getenv("YOUTUBE_API_KEY", ""),
        twitter_bearer_token=os.getenv("TWITTER_BEARER_TOKEN", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        fmp_api_key=os.getenv("FMP_API_KEY", ""),
    )
    db = DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        name=os.getenv("DB_NAME", "disney_dashboard"),
        user=os.getenv("DB_USER", "dashboard"),
        password=os.getenv("DB_PASSWORD", ""),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        elasticsearch_url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
    )
    ingestion = IngestionConfig()
    return api, db, ingestion
