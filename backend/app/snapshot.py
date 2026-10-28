"""Loads the committed JSON snapshot into indexed, typed structures."""

import json
from bisect import insort
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"


@dataclass(frozen=True)
class ForecastValue:
    publish_time: datetime
    generation: int


@dataclass
class Snapshot:
    first_day: date
    last_day: date
    actuals: dict[datetime, int]
    """Half-hourly actual wind generation (MW), keyed by startTime (UTC)."""
    forecasts: dict[datetime, list[ForecastValue]] = field(default_factory=dict)
    """Hourly forecasts keyed by startTime (UTC); each list is sorted by publish_time."""

    def delivery_days(self) -> list[date]:
        count = (self.last_day - self.first_day).days + 1
        return [self.first_day + timedelta(days=i) for i in range(count)]


def _read(path: Path) -> dict[str, Any]:
    content: dict[str, Any] = json.loads(path.read_text())
    return content


@lru_cache(maxsize=1)
def load_snapshot(data_dir: Path = DATA_DIR) -> Snapshot:
    actuals_file = _read(data_dir / "actuals.json")
    snapshot = Snapshot(
        first_day=date.fromisoformat(actuals_file["deliveryDays"]["from"]),
        last_day=date.fromisoformat(actuals_file["deliveryDays"]["to"]),
        actuals={
            datetime.fromisoformat(r["startTime"]): int(r["generation"])
            for r in actuals_file["records"]
        },
    )
    for r in _read(data_dir / "forecasts.json")["records"]:
        value = ForecastValue(datetime.fromisoformat(r["publishTime"]), int(r["generation"]))
        insort(
            snapshot.forecasts.setdefault(datetime.fromisoformat(r["startTime"]), []),
            value,
            key=lambda v: v.publish_time,
        )
    return snapshot
