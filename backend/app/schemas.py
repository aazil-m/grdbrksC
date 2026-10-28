"""API response models. Field names are camelCase in JSON."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class Health(ApiModel):
    status: str
    first_day: date
    last_day: date


class ActualPoint(ApiModel):
    start: datetime
    generation: int


class ForecastPoint(ApiModel):
    start: datetime
    actual: int | None
    forecast: int | None
    publish_time: datetime | None
    horizon_hours: float | None
    error: int | None


class Summary(ApiModel):
    count: int
    mae: float
    rmse: float
    bias: float
    nmae_pct: float | None
    p10: float
    p50: float
    p90: float
    max_abs_error: int


class DayResponse(ApiModel):
    date: date
    cutoff: str
    cutoff_utc: datetime
    actuals: list[ActualPoint]
    points: list[ForecastPoint]
    missing_hours: int
    summary: Summary | None


class RunPoint(ApiModel):
    start: datetime
    generation: int


class Run(ApiModel):
    publish_time: datetime
    is_decision_run: bool
    points: list[RunPoint]


class VintagesResponse(ApiModel):
    date: date
    cutoff: str
    cutoff_utc: datetime
    actuals: list[ActualPoint]
    runs: list[Run]


class Bin(ApiModel):
    lower: int
    upper: int
    count: int


class GroupStat(ApiModel):
    key: str
    count: int
    mae: float
    bias: float


class HorizonStat(ApiModel):
    lower_hours: int
    upper_hours: int
    count: int
    mae: float
    rmse: float
    bias: float


class MetricsResponse(ApiModel):
    cutoff: str
    summary: Summary | None
    total_hours: int
    missing_hours: int
    decision_horizon_min: float | None
    decision_horizon_max: float | None
    histogram: list[Bin]
    by_hour_of_day: list[GroupStat]
    by_day: list[GroupStat]
    by_horizon: list[HorizonStat]
    """Every forecast run by lead time (independent of the cutoff)."""
