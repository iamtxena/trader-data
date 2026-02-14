"""Contract tests for trader-data internal API routes."""

from fastapi.testclient import TestClient

from trader_data.internal_api import app


def _headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer service-key",
        "X-Tenant-Id": "tenant-a",
        "X-User-Id": "user-a",
        "X-Request-Id": "req-a",
    }


def test_internal_api_requires_service_auth_when_key_is_configured(monkeypatch) -> None:
    monkeypatch.setenv("TRADER_DATA_SERVICE_API_KEY", "service-key")
    client = TestClient(app)

    response = client.post(
        "/internal/v1/exports/backtest",
        json={"datasetIds": ["dataset-1"], "assetClasses": ["crypto"]},
    )

    assert response.status_code == 401


def test_create_and_get_backtest_export(monkeypatch) -> None:
    monkeypatch.setenv("TRADER_DATA_SERVICE_API_KEY", "service-key")
    client = TestClient(app)

    ingest = client.post(
        "/internal/v1/ingestion/candles",
        json={
            "schema_version": "1.0",
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "interval": "1m",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 12.0,
            "event_time": "2026-02-14T10:00:00Z",
        },
        headers=_headers(),
    )
    assert ingest.status_code == 200

    created = client.post(
        "/internal/v1/exports/backtest",
        json={"datasetIds": ["dataset-1"], "assetClasses": ["crypto"]},
        headers=_headers(),
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["status"] == "completed"
    assert payload["datasetIds"] == ["dataset-1"]
    assert payload["assetClasses"] == ["crypto"]
    assert "transformHash" in payload["lineage"]

    export_id = payload["id"]
    fetched = client.get(f"/internal/v1/exports/{export_id}", headers=_headers())
    assert fetched.status_code == 200
    assert fetched.json()["id"] == export_id


def test_market_context_and_transform_contract(monkeypatch) -> None:
    monkeypatch.setenv("TRADER_DATA_SERVICE_API_KEY", "service-key")
    client = TestClient(app)
    headers = _headers()

    client.post(
        "/internal/v1/ingestion/backfill/candles",
        json={
            "candles": [
                {
                    "schema_version": "1.0",
                    "symbol": "ETHUSDT",
                    "exchange": "binance",
                    "interval": "5m",
                    "open": 2000.0,
                    "high": 2010.0,
                    "low": 1995.0,
                    "close": 2008.0,
                    "volume": 20.0,
                    "event_time": "2026-02-14T10:00:00Z",
                },
                {
                    "schema_version": "1.0",
                    "symbol": "ETHUSDT",
                    "exchange": "binance",
                    "interval": "5m",
                    "open": 2008.0,
                    "high": 2020.0,
                    "low": 2001.0,
                    "close": 2018.0,
                    "volume": 25.0,
                    "event_time": "2026-02-14T10:05:00Z",
                },
            ]
        },
        headers=headers,
    )

    transform = client.post(
        "/internal/v1/transforms/candles",
        json={"symbol": "ETHUSDT", "interval": "5m", "minVolume": 0},
        headers=headers,
    )
    assert transform.status_code == 200
    assert transform.json()["itemCount"] >= 2
    assert transform.json()["outputHash"]

    context = client.post(
        "/internal/v1/context/market",
        json={"assetClasses": ["crypto"]},
        headers=headers,
    )
    assert context.status_code == 200
    body = context.json()
    assert "regimeSummary" in body
    assert "signals" in body
