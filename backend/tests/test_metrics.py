import math
from datetime import time

import pytest

from app.alignment import HourPoint
from app.metrics import (
    Bin,
    by_day,
    by_hour_of_day,
    error_by_horizon,
    evaluate,
    histogram,
    summarize,
)
from app.snapshot import Snapshot
from tests.conftest import utc


def point(hour: int, forecast: int, actual: int, day: int = 2) -> HourPoint:
    return HourPoint(
        start=utc(day, hour),
        actual=actual,
        forecast=forecast,
        publish_time=utc(1, 7, 30),
        horizon_hours=None,
        error=forecast - actual,
    )


# Errors: +100, -200, +300, -400 against actuals of 1000 each.
POINTS = [point(0, 1100, 1000), point(1, 800, 1000), point(2, 1300, 1000), point(3, 600, 1000)]


def test_summary_hand_worked() -> None:
    s = summarize(POINTS)
    assert s is not None
    assert s.count == 4
    assert s.mae == 250
    assert s.rmse == pytest.approx(math.sqrt((100**2 + 200**2 + 300**2 + 400**2) / 4))
    assert s.bias == -50
    assert s.nmae_pct == 25
    assert s.max_abs_error == 400
    # Inclusive deciles of [-400, -200, 100, 300]
    assert s.p50 == pytest.approx(-50)
    assert s.p10 == pytest.approx(-340)
    assert s.p90 == pytest.approx(240)


def test_summary_handles_empty_and_single_point() -> None:
    assert summarize([]) is None
    single = summarize([point(0, 1100, 1000)])
    assert single is not None and single.p10 == single.p90 == 100


def test_histogram_bins_are_contiguous_and_aligned() -> None:
    assert histogram([-400, -200, 100, 300, 1100], bin_width=500) == [
        Bin(-500, 0, 2),
        Bin(0, 500, 2),
        Bin(500, 1000, 0),
        Bin(1000, 1500, 1),
    ]
    assert histogram([]) == []


def test_group_by_hour_of_day_and_day() -> None:
    points = [point(0, 1100, 1000, day=2), point(0, 900, 1000, day=3), point(5, 1000, 1000)]
    hours = by_hour_of_day(points)
    assert [(g.key, g.count, g.mae, g.bias) for g in hours] == [("00", 2, 100, 0), ("05", 1, 0, 0)]
    days = by_day(points)
    assert [(g.key, g.count) for g in days] == [("2026-01-02", 2), ("2026-01-03", 1)]


def test_evaluate_excludes_and_reports_missing_hours(snapshot: Snapshot) -> None:
    report = evaluate(snapshot, time(1, 0))
    assert report.total_hours == 24
    assert report.missing_hours == 2
    assert report.summary is not None
    assert report.summary.count == 22
    assert report.summary.bias == 900 - 1100


def test_error_by_horizon_uses_every_run(snapshot: Snapshot) -> None:
    stats = error_by_horizon(snapshot, bin_hours=6)
    assert sum(s.count for s in stats) == 22 + 24 + 24
    # Run C (09:30 on 1 Jan) -> 2 Jan 00:00 is 14.5 h ahead, so the 12-18 h bin
    # holds run C's 00:00-03:00 targets (14.5..17.5 h) and run B's 00:00 target (16.5 h).
    twelve = next(s for s in stats if s.lower_hours == 12)
    assert twelve.count == 4 + 2
