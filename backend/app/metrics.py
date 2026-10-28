"""Forecast accuracy metrics. Error = forecast - actual (MW); positive = over-forecast."""

import math
import statistics
from collections import defaultdict
from collections.abc import Callable, Hashable, Iterable
from dataclasses import dataclass
from datetime import date, time

from app.alignment import UK, HourPoint, decision_forecast, hourly_targets
from app.snapshot import Snapshot

HISTOGRAM_BIN_MW = 500
HORIZON_BIN_HOURS = 6


@dataclass(frozen=True)
class Summary:
    count: int
    mae: float
    rmse: float
    bias: float
    nmae_pct: float
    """MAE as a percentage of the mean actual generation over the same points."""
    p10: float
    p50: float
    p90: float
    max_abs_error: int


@dataclass(frozen=True)
class Bin:
    lower: int
    upper: int
    count: int


@dataclass(frozen=True)
class GroupStat:
    key: str
    count: int
    mae: float
    bias: float


@dataclass(frozen=True)
class HorizonStat:
    lower_hours: int
    upper_hours: int
    count: int
    mae: float
    rmse: float
    bias: float


@dataclass(frozen=True)
class Report:
    summary: Summary | None
    total_hours: int
    missing_hours: int
    """Hours with no forecast published before the cutoff; excluded from all metrics."""
    histogram: list[Bin]
    by_hour_of_day: list[GroupStat]
    by_day: list[GroupStat]


def _mae(errors: list[int]) -> float:
    return sum(abs(e) for e in errors) / len(errors)


def _rmse(errors: list[int]) -> float:
    return math.sqrt(sum(e * e for e in errors) / len(errors))


def _bias(errors: list[int]) -> float:
    return sum(errors) / len(errors)


def complete(points: Iterable[HourPoint]) -> list[HourPoint]:
    """Points that have both a forecast and an actual."""
    return [p for p in points if p.error is not None]


def summarize(points: list[HourPoint]) -> Summary | None:
    errors = [p.error for p in points if p.error is not None]
    actuals = [p.actual for p in points if p.error is not None and p.actual is not None]
    if not errors:
        return None
    deciles = (
        statistics.quantiles(errors, n=10, method="inclusive")
        if len(errors) > 1
        else [float(errors[0])] * 9
    )
    mean_actual = sum(actuals) / len(actuals)
    return Summary(
        count=len(errors),
        mae=_mae(errors),
        rmse=_rmse(errors),
        bias=_bias(errors),
        nmae_pct=100 * _mae(errors) / mean_actual if mean_actual else math.nan,
        p10=deciles[0],
        p50=deciles[4],
        p90=deciles[8],
        max_abs_error=max(abs(e) for e in errors),
    )


def histogram(errors: list[int], bin_width: int = HISTOGRAM_BIN_MW) -> list[Bin]:
    """Contiguous bins aligned to multiples of bin_width, including empty bins."""
    if not errors:
        return []
    counts: dict[int, int] = defaultdict(int)
    for e in errors:
        counts[math.floor(e / bin_width) * bin_width] += 1
    lowest, highest = min(counts), max(counts)
    return [
        Bin(lower=b, upper=b + bin_width, count=counts.get(b, 0))
        for b in range(lowest, highest + bin_width, bin_width)
    ]


def _group(points: list[HourPoint], key: Callable[[HourPoint], Hashable]) -> list[GroupStat]:
    groups: dict[Hashable, list[int]] = defaultdict(list)
    for p in points:
        if p.error is not None:
            groups[key(p)].append(p.error)
    return [
        GroupStat(key=str(k), count=len(errs), mae=_mae(errs), bias=_bias(errs))
        for k, errs in sorted(groups.items(), key=lambda item: str(item[0]))
    ]


def by_hour_of_day(points: list[HourPoint]) -> list[GroupStat]:
    """Grouped by UK local hour of the target time, keyed "00".."23"."""
    return _group(points, lambda p: f"{p.start.astimezone(UK).hour:02d}")


def by_day(points: list[HourPoint]) -> list[GroupStat]:
    """Grouped by UK local delivery day, keyed by ISO date."""
    return _group(points, lambda p: p.start.astimezone(UK).date().isoformat())


def evaluate(snapshot: Snapshot, cutoff: time) -> Report:
    """Accuracy of the decision-time forecast over every delivery day in the snapshot."""
    points = [
        p for day in snapshot.delivery_days() for p in decision_forecast(snapshot, day, cutoff)
    ]
    usable = complete(points)
    return Report(
        summary=summarize(usable),
        total_hours=len(points),
        missing_hours=sum(1 for p in points if p.forecast is None),
        histogram=histogram([p.error for p in usable if p.error is not None]),
        by_hour_of_day=by_hour_of_day(usable),
        by_day=by_day(usable),
    )


def error_by_horizon(snapshot: Snapshot, bin_hours: int = HORIZON_BIN_HOURS) -> list[HorizonStat]:
    """Accuracy of every forecast run (not only decision-time runs) by lead time.

    Lead time = target time - publish time; forecasts published after their
    target time (negative lead time) are excluded.
    """
    days: list[date] = snapshot.delivery_days()
    groups: dict[int, list[int]] = defaultdict(list)
    for day in days:
        for target in hourly_targets(day):
            actual = snapshot.actuals.get(target)
            if actual is None:
                continue
            for v in snapshot.forecasts.get(target, []):
                hours = (target - v.publish_time).total_seconds() / 3600
                if hours >= 0:
                    groups[math.floor(hours / bin_hours) * bin_hours].append(v.generation - actual)
    return [
        HorizonStat(
            lower_hours=lower,
            upper_hours=lower + bin_hours,
            count=len(errs),
            mae=_mae(errs),
            rmse=_rmse(errs),
            bias=_bias(errs),
        )
        for lower, errs in sorted(groups.items())
    ]
