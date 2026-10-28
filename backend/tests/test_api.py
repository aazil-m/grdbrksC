"""API tests against the committed January 2026 snapshot."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get(path: str, **params: str) -> Any:
    response = client.get(path, params=params)
    assert response.status_code == 200, response.text
    return response.json()


def test_health() -> None:
    assert get("/api/health") == {"status": "ok", "firstDay": "2026-01-02", "lastDay": "2026-02-01"}


def test_day_returns_hourly_decision_points_and_half_hourly_actuals() -> None:
    body = get("/api/day", date="2026-01-15", cutoff="09:00")
    assert body["cutoffUtc"] == "2026-01-14T09:00:00Z"
    assert len(body["points"]) == 24 and len(body["actuals"]) == 48
    assert body["missingHours"] == 0
    first = body["points"][0]
    assert first["start"] == "2026-01-15T00:00:00Z"
    assert first["publishTime"] == "2026-01-14T07:30:00Z"
    assert first["error"] == first["forecast"] - first["actual"]
    assert body["summary"]["count"] == 24


def test_day_reports_missing_hours_for_early_cutoff() -> None:
    body = get("/api/day", date="2026-01-15", cutoff="01:00")
    assert body["missingHours"] == 2
    assert body["summary"]["count"] == 22


def test_vintages_mark_decision_run_and_hide_later_information() -> None:
    body = get("/api/vintages", date="2026-01-15", cutoff="09:00")
    decision = [r for r in body["runs"] if r["isDecisionRun"]]
    assert [r["publishTime"] for r in decision] == ["2026-01-14T07:30:00Z"]
    for run in body["runs"]:
        assert run["publishTime"] < "2026-01-16T00:00:00Z"
        assert all(p["start"] >= run["publishTime"] for p in run["points"])


def test_metrics_cover_all_delivery_days() -> None:
    body = get("/api/metrics", cutoff="09:00")
    assert body["totalHours"] == 31 * 24 and body["missingHours"] == 0
    assert len(body["byDay"]) == 31 and len(body["byHourOfDay"]) == 24
    assert sum(b["count"] for b in body["histogram"]) == body["summary"]["count"]
    assert body["byHorizon"][0]["lowerHours"] == 0
    # 09:00 cutoff -> the 07:30 run on D-1: 16.5 h to 00:00 and 39.5 h to 23:00 on D.
    assert (body["decisionHorizonMin"], body["decisionHorizonMax"]) == (16.5, 39.5)


@pytest.mark.parametrize(
    "path,params",
    [
        ("/api/day", {"date": "2026-01-15"}),
        ("/api/day", {"date": "2026-01-15", "cutoff": "9:00"}),
        ("/api/day", {"date": "2026-01-15", "cutoff": "24:00"}),
        ("/api/day", {"date": "2026-01-01", "cutoff": "09:00"}),
        ("/api/day", {"date": "2026-02-02", "cutoff": "09:00"}),
        ("/api/day", {"date": "not-a-date", "cutoff": "09:00"}),
        ("/api/vintages", {"date": "2026-01-15"}),
        ("/api/metrics", {}),
    ],
)
def test_invalid_input_is_rejected(path: str, params: dict[str, str]) -> None:
    assert client.get(path, params=params).status_code == 422
