import json
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pytest

from ingest.elexon import BASE_URL, ElexonClient
from ingest.snapshot import clean_actuals, clean_forecasts, write_json


def _client(handler: Any) -> ElexonClient:
    http = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler))
    return ElexonClient(client=http, max_attempts=3, backoff_seconds=0)


def test_client_retries_retryable_status_then_succeeds() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) < 3:
            return httpx.Response(503)
        return httpx.Response(200, json=[{"startTime": "x"}])

    from datetime import date

    assert _client(handler).wind_actuals(date(2026, 1, 2)) == [{"startTime": "x"}]
    assert len(calls) == 3
    assert calls[0].url.params["fuelType"] == "WIND"
    assert calls[0].url.params["settlementDateFrom"] == "2026-01-02"


def test_client_raises_after_max_attempts() -> None:

    with pytest.raises(httpx.HTTPStatusError):
        _client(lambda _: httpx.Response(503)).wind_actuals(date(2026, 1, 2))


def test_client_does_not_retry_client_errors() -> None:

    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(400)

    with pytest.raises(httpx.HTTPStatusError):
        _client(handler).wind_actuals(date(2026, 1, 2))
    assert len(calls) == 1


def test_clean_actuals_keeps_latest_publish_and_sorts() -> None:
    raw = [
        {"startTime": "T2", "publishTime": "P1", "fuelType": "WIND", "generation": 5},
        {"startTime": "T1", "publishTime": "P1", "fuelType": "WIND", "generation": 1},
        {"startTime": "T1", "publishTime": "P2", "fuelType": "WIND", "generation": 2},
        {"startTime": "T1", "publishTime": "P3", "fuelType": "CCGT", "generation": 99},
    ]
    assert clean_actuals(raw) == [
        {"startTime": "T1", "publishTime": "P2", "generation": 2},
        {"startTime": "T2", "publishTime": "P1", "generation": 5},
    ]


def test_clean_forecasts_filters_target_window_and_dedupes() -> None:
    raw = [
        {
            "publishTime": "2026-01-01T07:30:00Z",
            "startTime": "2026-01-01T23:00:00Z",
            "generation": 1,
        },
        {
            "publishTime": "2026-01-01T07:30:00Z",
            "startTime": "2026-01-02T00:00:00Z",
            "generation": 2,
        },
        {
            "publishTime": "2026-01-01T07:30:00Z",
            "startTime": "2026-01-02T00:00:00Z",
            "generation": 2,
        },
        {
            "publishTime": "2026-01-01T07:30:00Z",
            "startTime": "2026-02-02T00:00:00Z",
            "generation": 3,
        },
    ]
    result = clean_forecasts(raw, "2026-01-02T00:00:00Z", "2026-02-02T00:00:00Z")
    assert result == [
        {
            "publishTime": "2026-01-01T07:30:00Z",
            "startTime": "2026-01-02T00:00:00Z",
            "generation": 2,
        }
    ]


def test_write_json_produces_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "out.json"
    records = [{"startTime": "T1", "generation": 1}, {"startTime": "T2", "generation": 2}]
    write_json(path, {"source": "test", "units": "MW"}, records)
    assert json.loads(path.read_text()) == {"source": "test", "units": "MW", "records": records}
