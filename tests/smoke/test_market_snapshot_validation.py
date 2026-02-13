"""Schema/model smoke tests for market snapshot validation."""

from datetime import timezone

import pytest

from trader_data.models.market_snapshot import MarketSnapshotV1


def test_market_snapshot_accepts_valid_payload() -> None:
    payload = {
        "schema_version": "1.0",
        "symbol": "btc-usd",
        "event_time": "2026-02-13T10:00:00Z",
        "ingest_time": "2026-02-13T10:00:01Z",
        "price": 100_000.5,
        "volume": 1.25,
        "source": "provider-sim",
    }

    snapshot = MarketSnapshotV1.from_payload(payload)

    assert snapshot.schema_version == "1.0"
    assert snapshot.symbol == "BTC-USD"
    assert snapshot.event_time.tzinfo == timezone.utc
    assert snapshot.ingest_time.tzinfo == timezone.utc
    assert snapshot.price == pytest.approx(100_000.5)
    assert snapshot.volume == pytest.approx(1.25)
    assert snapshot.source == "provider-sim"


def test_market_snapshot_rejects_invalid_payload() -> None:
    payload = {
        "schema_version": "1.0",
        "symbol": "ETH-USD",
        "event_time": "2026-02-13T10:00:00Z",
        "ingest_time": "2026-02-13T09:59:59Z",
        "price": 2500.0,
        "source": "provider-sim",
    }

    with pytest.raises(ValueError):
        MarketSnapshotV1.from_payload(payload)
