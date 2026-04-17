"""Park wait times connector — fetches ride wait times from Queue-Times API."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from disney_dashboard.ingestion.base import BaseConnector
from disney_dashboard.models.schemas import Signal, SourceType


class ParkWaitTimesConnector(BaseConnector):
    source_type = SourceType.PARK_API
    source_name = "queue_times"

    BASE_URL = "https://queue-times.com/parks"

    PARK_IDS: Dict[str, int] = {
        "Magic Kingdom": 6,
        "EPCOT": 5,
        "Hollywood Studios": 7,
        "Animal Kingdom": 8,
        "Disneyland Park": 16,
        "Disney California Adventure": 17,
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(rate_limit=0.2, **kwargs)

    async def fetch(self) -> List[Signal]:
        signals: List[Signal] = []

        for park_name, park_id in self.PARK_IDS.items():
            try:
                data = await self._request(
                    f"{self.BASE_URL}/{park_id}/queue_times.json",
                    headers={"Accept": "application/json"},
                )

                rides = data.get("rides", [])
                if not rides:
                    lands = data.get("lands", [])
                    for land in lands:
                        rides.extend(land.get("rides", []))

                wait_times: List[int] = []
                ride_details: List[Dict] = []

                for ride in rides:
                    wait = ride.get("wait_time", 0)
                    is_open = ride.get("is_open", False)
                    ride_info = {
                        "name": ride.get("name", ""),
                        "wait_time": wait,
                        "is_open": is_open,
                    }
                    ride_details.append(ride_info)
                    if is_open and wait > 0:
                        wait_times.append(wait)

                avg_wait = round(sum(wait_times) / len(wait_times), 1) if wait_times else 0
                max_wait = max(wait_times) if wait_times else 0
                open_rides = sum(1 for r in ride_details if r["is_open"])

                signals.append(
                    Signal(
                        source_type=self.source_type,
                        source_name=self.source_name,
                        source_url=f"https://queue-times.com/parks/{park_id}",
                        title=f"{park_name} Wait Times Snapshot",
                        body=(
                            f"Average wait: {avg_wait} min | "
                            f"Max wait: {max_wait} min | "
                            f"Open rides: {open_rides}/{len(ride_details)}"
                        ),
                        published_at=datetime.utcnow(),
                        raw_payload={
                            "park_name": park_name,
                            "park_id": park_id,
                            "avg_wait": avg_wait,
                            "max_wait": max_wait,
                            "open_rides": open_rides,
                            "total_rides": len(ride_details),
                            "rides": ride_details,
                        },
                    )
                )
            except Exception as exc:
                self.logger.warning(
                    "Wait times fetch failed for %s: %s", park_name, exc
                )

        self.logger.info("Queue-Times returned data for %d parks", len(signals))
        return signals
