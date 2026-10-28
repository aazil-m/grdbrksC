"""Selects the forecast that was available at the day-ahead decision time.

Rule: for each hourly target time t in delivery day D (UK local day), use the
forecast with the largest publishTime that is <= the cutoff on D-1 (UK time).
Error = forecast - actual, in MW, at hourly points only.
"""

from bisect import bisect_right
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.snapshot import Snapshot

UK = ZoneInfo("Europe/London")


@dataclass(frozen=True)
class HourPoint:
    start: datetime
    actual: int | None
    forecast: int | None
    publish_time: datetime | None
    horizon_hours: float | None
    error: int | None
    """forecast - actual (MW); None when either value is missing."""


def cutoff_datetime(day: date, cutoff: time) -> datetime:
    """The decision cutoff for delivery day `day`: `cutoff` UK time on the day before (UTC)."""
    return datetime.combine(day - timedelta(days=1), cutoff, tzinfo=UK).astimezone(UTC)


def _local_day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=UK).astimezone(UTC)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=UK).astimezone(UTC)
    return start, end


def hourly_targets(day: date) -> list[datetime]:
    """UTC hourly target times making up the UK local delivery day (23/24/25 hours)."""
    start, end = _local_day_bounds(day)
    return [start + timedelta(hours=h) for h in range(int((end - start).total_seconds()) // 3600)]


def day_actuals(snapshot: Snapshot, day: date) -> list[tuple[datetime, int]]:
    """Half-hourly actuals within the UK local delivery day."""
    start, end = _local_day_bounds(day)
    return sorted((t, g) for t, g in snapshot.actuals.items() if start <= t < end)


def decision_forecast(snapshot: Snapshot, day: date, cutoff: time) -> list[HourPoint]:
    cutoff_at = cutoff_datetime(day, cutoff)
    points = []
    for target in hourly_targets(day):
        actual = snapshot.actuals.get(target)
        values = snapshot.forecasts.get(target, [])
        index = bisect_right(values, cutoff_at, key=lambda v: v.publish_time)
        chosen = values[index - 1] if index > 0 else None
        points.append(
            HourPoint(
                start=target,
                actual=actual,
                forecast=chosen.generation if chosen else None,
                publish_time=chosen.publish_time if chosen else None,
                horizon_hours=(
                    (target - chosen.publish_time).total_seconds() / 3600 if chosen else None
                ),
                error=(
                    chosen.generation - actual
                    if chosen is not None and actual is not None
                    else None
                ),
            )
        )
    return points


def vintages(snapshot: Snapshot, day: date) -> dict[datetime, list[tuple[datetime, int]]]:
    """Every forecast run with values for the delivery day: publish_time -> [(start, MW)]."""
    targets = hourly_targets(day)
    runs: dict[datetime, list[tuple[datetime, int]]] = {}
    for target in targets:
        for v in snapshot.forecasts.get(target, []):
            runs.setdefault(v.publish_time, []).append((target, v.generation))
    return dict(sorted(runs.items()))
