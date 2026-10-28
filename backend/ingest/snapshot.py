"""Builds the January 2026 snapshot (purchase decisions made 1-31 Jan 2026).

Delivery days are 2 Jan - 1 Feb 2026. Forecast runs are taken from those
published 31 Dec 2025 - 1 Feb 2026, which covers every run targeting that range.
All timestamps are UTC ISO-8601 strings, exactly as returned by Elexon.
"""

import json
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from ingest.elexon import ElexonClient, daterange

DELIVERY_START = date(2026, 1, 2)
DELIVERY_END = date(2026, 2, 1)
FORECAST_PUBLISH_START = date(2025, 12, 31)
FORECAST_PUBLISH_END = date(2026, 2, 1)

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"

Record = dict[str, Any]


def _utc_iso(d: date) -> str:
    return datetime.combine(d, time.min, tzinfo=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean_actuals(raw: list[Record]) -> list[Record]:
    """Keeps the latest publishTime per startTime (Elexon may resubmit values)."""
    latest: dict[str, Record] = {}
    for r in raw:
        if r.get("fuelType") != "WIND":
            continue
        current = latest.get(r["startTime"])
        if current is None or r["publishTime"] > current["publishTime"]:
            latest[r["startTime"]] = r
    return [
        {
            "startTime": r["startTime"],
            "publishTime": r["publishTime"],
            "generation": r["generation"],
        }
        for r in sorted(latest.values(), key=lambda r: r["startTime"])
    ]


def clean_forecasts(raw: list[Record], target_from: str, target_to: str) -> list[Record]:
    """Dedupes on (publishTime, startTime) and keeps targets in [target_from, target_to)."""
    unique: dict[tuple[str, str], Record] = {}
    for r in raw:
        if target_from <= r["startTime"] < target_to:
            unique[(r["publishTime"], r["startTime"])] = r
    return [
        {"publishTime": p, "startTime": s, "generation": r["generation"]}
        for (p, s), r in sorted(unique.items())
    ]


def build(client: ElexonClient) -> tuple[list[Record], list[Record]]:
    raw_actuals: list[Record] = []
    for day in daterange(DELIVERY_START, DELIVERY_END):
        raw_actuals.extend(client.wind_actuals(day))

    raw_forecasts: list[Record] = []
    for day in daterange(FORECAST_PUBLISH_START, FORECAST_PUBLISH_END):
        start = datetime.combine(day, time.min, tzinfo=UTC)
        raw_forecasts.extend(client.wind_forecasts(start, start + timedelta(days=1, seconds=-1)))

    target_from = _utc_iso(DELIVERY_START)
    target_to = _utc_iso(DELIVERY_END + timedelta(days=1))
    return clean_actuals(raw_actuals), clean_forecasts(raw_forecasts, target_from, target_to)


def write_json(path: Path, meta: dict[str, Any], records: list[Record]) -> None:
    """One record per line: compact, but readable and diff-friendly."""
    lines = ",\n".join("    " + json.dumps(r, separators=(",", ":")) for r in records)
    header = json.dumps(meta, indent=2)[:-2]
    path.write_text(f'{header},\n  "records": [\n{lines}\n  ]\n}}\n')
