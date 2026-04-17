"""Entity resolver — maps signals to Disney business units and properties."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from disney_dashboard.config.settings import COMPETITORS, DISNEY_ENTITIES
from disney_dashboard.models.schemas import Signal
from disney_dashboard.utils.logging import get_logger

logger = get_logger("entity_resolver")


@dataclass
class EntityMatch:
    entity_name: str
    entity_type: str  # business_unit, property, competitor, topic
    relevance_score: float
    matched_term: str


class EntityResolver:
    def __init__(self) -> None:
        self._patterns: List[Tuple[re.Pattern, str, str]] = []
        self._build_patterns()

    def _build_patterns(self) -> None:
        for business_unit, properties in DISNEY_ENTITIES.items():
            pattern = re.compile(re.escape(business_unit), re.IGNORECASE)
            self._patterns.append((pattern, business_unit, "business_unit"))

            for prop in properties:
                pattern = re.compile(re.escape(prop), re.IGNORECASE)
                self._patterns.append((pattern, prop, "property"))

        for competitor in COMPETITORS:
            pattern = re.compile(re.escape(competitor), re.IGNORECASE)
            self._patterns.append((pattern, competitor, "competitor"))

        topic_patterns = {
            "pricing": r"\b(ticket price|pricing|price increase|price hike|cost)\b",
            "attendance": r"\b(attendance|crowd|visitor|guest count|capacity)\b",
            "new_attractions": r"\b(new ride|new attraction|opening|grand opening|construction)\b",
            "labor": r"\b(cast member|employee|union|wage|strike|hiring|layoff)\b",
            "guest_satisfaction": r"\b(guest experience|review|complaint|satisfaction|rating)\b",
            "lightning_lane": r"\b(lightning lane|genie\+|genie plus|fastpass|fast pass)\b",
            "food_bev": r"\b(restaurant|dining|food|menu|snack|reservation)\b",
            "hotel": r"\b(hotel|resort hotel|deluxe resort|moderate resort|value resort|hotel occupancy)\b",
            "earnings": r"\b(earnings|revenue|profit|quarterly results|fiscal|financial)\b",
            "expansion": r"\b(expansion|new land|construction|imagineering|D23)\b",
        }
        for topic, pattern_str in topic_patterns.items():
            pattern = re.compile(pattern_str, re.IGNORECASE)
            self._patterns.append((pattern, topic, "topic"))

    def resolve(self, signal: Signal) -> List[EntityMatch]:
        text = f"{signal.title} {signal.body}"
        matches: Dict[str, EntityMatch] = {}

        for pattern, entity_name, entity_type in self._patterns:
            found = pattern.findall(text)
            if found:
                count = len(found)
                relevance = min(1.0, 0.5 + count * 0.1)

                key = f"{entity_type}:{entity_name}"
                if key not in matches or matches[key].relevance_score < relevance:
                    matches[key] = EntityMatch(
                        entity_name=entity_name,
                        entity_type=entity_type,
                        relevance_score=relevance,
                        matched_term=found[0] if found else entity_name,
                    )

        return list(matches.values())

    def resolve_batch(self, signals: List[Signal]) -> Dict[str, List[EntityMatch]]:
        results: Dict[str, List[EntityMatch]] = {}
        for signal in signals:
            entity_matches = self.resolve(signal)
            results[str(signal.id)] = entity_matches

        total_matches = sum(len(m) for m in results.values())
        logger.info(
            "Entity resolution: %d signals → %d total entity matches",
            len(signals), total_matches,
        )
        return results
