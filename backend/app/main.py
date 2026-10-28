"""FastAPI application: day-ahead wind forecast monitoring for January 2026."""

from datetime import date, time
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, Query

from app import alignment, metrics, schemas
from app.snapshot import Snapshot, load_snapshot

CutoffParam = Annotated[
    str,
    Query(
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
        description="Decision cutoff, UK local time (HH:MM) on the day before delivery.",
        examples=["09:00"],
    ),
]
DateParam = Annotated[date, Query(description="Delivery day (UK local), YYYY-MM-DD.")]

router = APIRouter(prefix="/api")


def _snapshot() -> Snapshot:
    return load_snapshot()


def _checked_day(day: date) -> date:
    snapshot = _snapshot()
    if not snapshot.first_day <= day <= snapshot.last_day:
        raise HTTPException(
            status_code=422,
            detail=f"date must be between {snapshot.first_day} and {snapshot.last_day}",
        )
    return day


@lru_cache(maxsize=256)
def _report(cutoff: time) -> metrics.Report:
    return metrics.evaluate(_snapshot(), cutoff)


@lru_cache(maxsize=1)
def _by_horizon() -> list[metrics.HorizonStat]:
    return metrics.error_by_horizon(_snapshot())


def _actuals(day: date) -> list[schemas.ActualPoint]:
    return [
        schemas.ActualPoint(start=start, generation=generation)
        for start, generation in alignment.day_actuals(_snapshot(), day)
    ]


@router.get("/health", response_model=schemas.Health)
def health() -> schemas.Health:
    snapshot = _snapshot()
    return schemas.Health(status="ok", first_day=snapshot.first_day, last_day=snapshot.last_day)


@router.get("/day", response_model=schemas.DayResponse)
def day_view(date: DateParam, cutoff: CutoffParam) -> schemas.DayResponse:
    day, cutoff_time = _checked_day(date), time.fromisoformat(cutoff)
    points = alignment.decision_forecast(_snapshot(), day, cutoff_time)
    summary = metrics.summarize(metrics.complete(points))
    return schemas.DayResponse(
        date=day,
        cutoff=cutoff,
        cutoff_utc=alignment.cutoff_datetime(day, cutoff_time),
        actuals=_actuals(day),
        points=[schemas.ForecastPoint.model_validate(p) for p in points],
        missing_hours=sum(1 for p in points if p.forecast is None),
        summary=schemas.Summary.model_validate(summary) if summary else None,
    )


@router.get("/vintages", response_model=schemas.VintagesResponse)
def vintages_view(date: DateParam, cutoff: CutoffParam) -> schemas.VintagesResponse:
    day, cutoff_time = _checked_day(date), time.fromisoformat(cutoff)
    snapshot = _snapshot()
    decision_runs = {
        p.publish_time for p in alignment.decision_forecast(snapshot, day, cutoff_time)
    }
    return schemas.VintagesResponse(
        date=day,
        cutoff=cutoff,
        cutoff_utc=alignment.cutoff_datetime(day, cutoff_time),
        actuals=_actuals(day),
        runs=[
            schemas.Run(
                publish_time=publish_time,
                is_decision_run=publish_time in decision_runs,
                points=[schemas.RunPoint(start=s, generation=g) for s, g in points],
            )
            for publish_time, points in alignment.vintages(snapshot, day).items()
        ],
    )


@router.get("/metrics", response_model=schemas.MetricsResponse)
def metrics_view(cutoff: CutoffParam) -> schemas.MetricsResponse:
    report = _report(time.fromisoformat(cutoff))
    return schemas.MetricsResponse(
        cutoff=cutoff,
        summary=schemas.Summary.model_validate(report.summary) if report.summary else None,
        total_hours=report.total_hours,
        missing_hours=report.missing_hours,
        decision_horizon_min=report.decision_horizon_min,
        decision_horizon_max=report.decision_horizon_max,
        histogram=[schemas.Bin.model_validate(b) for b in report.histogram],
        by_hour_of_day=[schemas.GroupStat.model_validate(g) for g in report.by_hour_of_day],
        by_day=[schemas.GroupStat.model_validate(g) for g in report.by_day],
        by_horizon=[schemas.HorizonStat.model_validate(h) for h in _by_horizon()],
    )


app = FastAPI(
    title="UK Wind Forecast Monitor",
    description="Day-ahead wind forecast vs actual generation (Elexon BMRS), January 2026.",
    version="0.1.0",
    # Served under /api so the docs are reachable behind the same routing as the API.
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)
app.include_router(router)
