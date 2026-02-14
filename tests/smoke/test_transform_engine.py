"""Smoke tests for deterministic transform engine behavior."""

from trader_data.ingestion import IngestionPipeline
from trader_data.store import InMemoryDataStore
from trader_data.transforms import TransformEngine


def test_transform_engine_output_hash_is_reproducible() -> None:
    store = InMemoryDataStore()
    ingestion = IngestionPipeline(store)
    engine = TransformEngine()
    payloads = [
        {
            "schema_version": "1.0",
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "interval": "1m",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 5.0,
            "event_time": "2026-02-14T10:00:00Z",
        },
        {
            "schema_version": "1.0",
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "interval": "1m",
            "open": 100.0,
            "high": 104.0,
            "low": 99.0,
            "close": 102.0,
            "volume": 8.0,
            "event_time": "2026-02-14T10:01:00Z",
        },
    ]
    for payload in payloads:
        ingestion.ingest_candle(payload)

    first = engine.transform_candles(candles=list(store.candles), min_volume=0.0)
    second = engine.transform_candles(candles=list(store.candles), min_volume=0.0)
    assert first.output_hash == second.output_hash
    assert first.items == second.items


def test_transform_engine_filters_by_volume() -> None:
    store = InMemoryDataStore()
    ingestion = IngestionPipeline(store)
    engine = TransformEngine()
    ingestion.ingest_candle(
        {
            "schema_version": "1.0",
            "symbol": "ETHUSDT",
            "exchange": "binance",
            "interval": "5m",
            "open": 2000.0,
            "high": 2010.0,
            "low": 1990.0,
            "close": 2005.0,
            "volume": 0.5,
            "event_time": "2026-02-14T10:00:00Z",
        }
    )
    result = engine.transform_candles(candles=list(store.candles), min_volume=1.0)
    assert result.item_count == 0
    assert result.items == []
