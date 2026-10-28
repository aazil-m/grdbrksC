from datetime import UTC, date, datetime

import pytest

from app.snapshot import ForecastValue, Snapshot


def utc(day: int, hour: int, minute: int = 0, month: int = 1) -> datetime:
    return datetime(2026, month, day, hour, minute, tzinfo=UTC)


@pytest.fixture
def snapshot() -> Snapshot:
    """Delivery day 2026-01-02 with three runs.

    - run A, published 31 Dec 22:30: covers 2 Jan only up to 21:00
    - run B, published 1 Jan 07:30: covers all of 2 Jan, forecast 1000 MW
    - run C, published 1 Jan 09:30: covers all of 2 Jan, forecast 1200 MW
    Actuals are 1100 MW every half-hour.
    """
    run_a = datetime(2025, 12, 31, 22, 30, tzinfo=UTC)
    run_b, run_c = utc(1, 7, 30), utc(1, 9, 30)
    forecasts: dict[datetime, list[ForecastValue]] = {}
    for hour in range(24):
        values = [ForecastValue(run_b, 1000), ForecastValue(run_c, 1200)]
        if hour <= 21:
            values.insert(0, ForecastValue(run_a, 900))
        forecasts[utc(2, hour)] = values
    actuals = {utc(2, h, m): 1100 for h in range(24) for m in (0, 30)}
    return Snapshot(
        first_day=date(2026, 1, 2), last_day=date(2026, 1, 2), actuals=actuals, forecasts=forecasts
    )
