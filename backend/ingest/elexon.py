"""Minimal Elexon BMRS client for the FUELHH and WINDFOR stream endpoints."""

import time
from datetime import date, datetime, timedelta
from typing import Any

import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class ElexonClient:
    def __init__(
        self,
        client: httpx.Client | None = None,
        max_attempts: int = 4,
        backoff_seconds: float = 1.0,
    ) -> None:
        self._client = client or httpx.Client(base_url=BASE_URL, timeout=60.0)
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds

    def _get(self, path: str, params: dict[str, str]) -> list[dict[str, Any]]:
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = self._client.get(path, params=params)
            except httpx.TransportError:
                if attempt == self._max_attempts:
                    raise
            else:
                if response.status_code not in RETRYABLE_STATUS or attempt == self._max_attempts:
                    response.raise_for_status()
                    data: list[dict[str, Any]] = response.json()
                    return data
            time.sleep(self._backoff_seconds * 2 ** (attempt - 1))
        raise RuntimeError("unreachable")

    def wind_actuals(self, settlement_date: date) -> list[dict[str, Any]]:
        """FUELHH WIND records for one settlement date."""
        day = settlement_date.isoformat()
        return self._get(
            "/FUELHH/stream",
            {"settlementDateFrom": day, "settlementDateTo": day, "fuelType": "WIND"},
        )

    def wind_forecasts(self, publish_from: datetime, publish_to: datetime) -> list[dict[str, Any]]:
        """WINDFOR records whose publishTime falls in [publish_from, publish_to]."""
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        return self._get(
            "/WINDFOR/stream",
            {
                "publishDateTimeFrom": publish_from.strftime(fmt),
                "publishDateTimeTo": publish_to.strftime(fmt),
            },
        )


def daterange(start: date, end: date) -> list[date]:
    """Inclusive list of dates from start to end."""
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]
