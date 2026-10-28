from datetime import UTC, date, datetime, time

from app.alignment import cutoff_datetime, day_actuals, decision_forecast, hourly_targets, vintages
from app.snapshot import Snapshot
from tests.conftest import utc

DAY = date(2026, 1, 2)


def test_cutoff_is_uk_time_on_the_previous_day() -> None:
    assert cutoff_datetime(DAY, time(9, 0)) == utc(1, 9)
    # During BST the UK is UTC+1.
    assert cutoff_datetime(date(2026, 7, 2), time(9, 0)) == datetime(2026, 7, 1, 8, tzinfo=UTC)


def test_hourly_targets_follow_uk_local_day_including_clock_changes() -> None:
    assert len(hourly_targets(DAY)) == 24
    assert hourly_targets(DAY)[0] == utc(2, 0)
    assert len(hourly_targets(date(2026, 3, 29))) == 23  # clocks go forward
    assert len(hourly_targets(date(2026, 10, 25))) == 25  # clocks go back


def test_uses_latest_run_published_at_or_before_cutoff(snapshot: Snapshot) -> None:
    points = decision_forecast(snapshot, DAY, time(9, 0))
    assert {p.forecast for p in points} == {1000}
    assert {p.publish_time for p in points} == {utc(1, 7, 30)}


def test_run_published_exactly_at_cutoff_is_included(snapshot: Snapshot) -> None:
    points = decision_forecast(snapshot, DAY, time(9, 30))
    assert {p.forecast for p in points} == {1200}


def test_hours_without_a_run_before_cutoff_are_missing(snapshot: Snapshot) -> None:
    points = decision_forecast(snapshot, DAY, time(1, 0))
    covered = [p for p in points if p.forecast is not None]
    missing = [p for p in points if p.forecast is None]
    assert len(covered) == 22 and {p.forecast for p in covered} == {900}
    assert [p.start for p in missing] == [utc(2, 22), utc(2, 23)]
    assert all(p.error is None and p.horizon_hours is None for p in missing)


def test_error_and_horizon(snapshot: Snapshot) -> None:
    first = decision_forecast(snapshot, DAY, time(9, 0))[0]
    assert first.actual == 1100
    assert first.error == 1000 - 1100
    assert first.horizon_hours == 16.5  # 1 Jan 07:30 -> 2 Jan 00:00


def test_day_actuals_are_half_hourly_and_within_the_day(snapshot: Snapshot) -> None:
    actuals = day_actuals(snapshot, DAY)
    assert len(actuals) == 48
    assert actuals[0] == (utc(2, 0), 1100) and actuals[-1] == (utc(2, 23, 30), 1100)


def test_vintages_lists_every_run_in_publish_order(snapshot: Snapshot) -> None:
    runs = vintages(snapshot, DAY)
    assert list(runs) == [datetime(2025, 12, 31, 22, 30, tzinfo=UTC), utc(1, 7, 30), utc(1, 9, 30)]
    assert len(runs[utc(1, 7, 30)]) == 24
    assert len(runs[datetime(2025, 12, 31, 22, 30, tzinfo=UTC)]) == 22
