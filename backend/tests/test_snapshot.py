"""Integrity checks on the committed snapshot in app/data."""

import json
from collections import defaultdict
from datetime import UTC, datetime, time, timedelta
from typing import Any

from app.metrics import evaluate
from app.snapshot import load_snapshot
from ingest.snapshot import DATA_DIR, DELIVERY_END, DELIVERY_START

FMT = "%Y-%m-%dT%H:%M:%SZ"


def _load(name: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = json.loads((DATA_DIR / name).read_text())["records"]
    return records


def _delivery_days() -> list[datetime]:
    days = (DELIVERY_END - DELIVERY_START).days + 1
    start = datetime(DELIVERY_START.year, DELIVERY_START.month, DELIVERY_START.day, tzinfo=UTC)
    return [start + timedelta(days=i) for i in range(days)]


def test_actuals_cover_every_half_hour_of_delivery_range() -> None:
    expected = [
        (day + timedelta(minutes=30 * i)).strftime(FMT)
        for day in _delivery_days()
        for i in range(48)
    ]
    assert [r["startTime"] for r in _load("actuals.json")] == expected


def test_every_day_ahead_run_covers_the_whole_delivery_day() -> None:
    runs: dict[str, set[str]] = defaultdict(set)
    for r in _load("forecasts.json"):
        runs[r["publishTime"]].add(r["startTime"])

    for day in _delivery_days():
        previous_day = (day - timedelta(days=1)).strftime("%Y-%m-%d")
        day_ahead_runs = [p for p in runs if p.startswith(previous_day)]
        hours = {(day + timedelta(hours=h)).strftime(FMT) for h in range(24)}
        assert day_ahead_runs, f"no forecast runs published on {previous_day}"
        for publish_time in day_ahead_runs:
            assert hours <= runs[publish_time], f"run {publish_time} misses hours of {day:%Y-%m-%d}"


def test_real_data_missing_hours_depend_on_cutoff() -> None:
    snapshot = load_snapshot()
    # Before the first run of D-1 (02:30), the latest run is D-2 22:30, which
    # only reaches 21:00 on D: hours 22 and 23 are missing on each of the 31 days.
    assert evaluate(snapshot, time(2, 29)).missing_hours == 2 * 31
    assert evaluate(snapshot, time(2, 30)).missing_hours == 0
