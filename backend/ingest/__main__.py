"""Usage: python -m ingest"""

from datetime import UTC, datetime

from ingest.elexon import BASE_URL, ElexonClient
from ingest.snapshot import (
    DATA_DIR,
    DELIVERY_END,
    DELIVERY_START,
    FORECAST_PUBLISH_END,
    FORECAST_PUBLISH_START,
    build,
    write_json,
)


def main() -> None:
    actuals, forecasts = build(ElexonClient())
    fetched_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    delivery = {"from": DELIVERY_START.isoformat(), "to": DELIVERY_END.isoformat()}

    write_json(
        DATA_DIR / "actuals.json",
        {
            "source": f"{BASE_URL}/FUELHH/stream (fuelType=WIND)",
            "fetchedAt": fetched_at,
            "deliveryDays": delivery,
            "units": "MW",
        },
        actuals,
    )
    write_json(
        DATA_DIR / "forecasts.json",
        {
            "source": f"{BASE_URL}/WINDFOR/stream",
            "fetchedAt": fetched_at,
            "deliveryDays": delivery,
            "publishDays": {
                "from": FORECAST_PUBLISH_START.isoformat(),
                "to": FORECAST_PUBLISH_END.isoformat(),
            },
            "units": "MW",
        },
        forecasts,
    )
    runs = len({f["publishTime"] for f in forecasts})
    print(f"actuals: {len(actuals)} records | forecasts: {len(forecasts)} records in {runs} runs")


if __name__ == "__main__":
    main()
