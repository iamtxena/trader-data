"""Smoke tests for ingestion pipeline determinism."""

import pytest

from trader_data.ingestion import IngestionPipeline
from trader_data.store import InMemoryDataStore


def test_candle_backfill_is_deterministically_sorted() -> None:
    store = InMemoryDataStore()
    pipeline = IngestionPipeline(store)
    candles = pipeline.backfill_candles(
        [
            {
                "schema_version": "1.0",
                "symbol": "BTCUSDT",
                "exchange": "binance",
                "interval": "1m",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 10.0,
                "event_time": "2026-02-14T10:00:03Z",
            },
            {
                "schema_version": "1.0",
                "symbol": "BTCUSDT",
                "exchange": "binance",
                "interval": "1m",
                "open": 99.0,
                "high": 100.0,
                "low": 98.0,
                "close": 99.8,
                "volume": 8.0,
                "event_time": "2026-02-14T10:00:01Z",
            },
        ]
    )
    assert [item.event_time.isoformat().replace("+00:00", "Z") for item in candles] == [
        "2026-02-14T10:00:01Z",
        "2026-02-14T10:00:03Z",
    ]


def test_candle_backfill_sorts_with_exchange_tiebreaker() -> None:
    store = InMemoryDataStore()
    pipeline = IngestionPipeline(store)
    candles = pipeline.backfill_candles(
        [
            {
                "schema_version": "1.0",
                "symbol": "BTCUSDT",
                "exchange": "coinbase",
                "interval": "1m",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 10.0,
                "event_time": "2026-02-14T10:00:01Z",
            },
            {
                "schema_version": "1.0",
                "symbol": "BTCUSDT",
                "exchange": "binance",
                "interval": "1m",
                "open": 99.0,
                "high": 100.0,
                "low": 98.0,
                "close": 99.8,
                "volume": 8.0,
                "event_time": "2026-02-14T10:00:01Z",
            },
        ]
    )
    assert [item.exchange for item in candles] == ["binance", "coinbase"]


def test_tick_ingestion_defaults_schema_version() -> None:
    store = InMemoryDataStore()
    pipeline = IngestionPipeline(store)
    tick = pipeline.ingest_tick(
        {
            "symbol": "ETHUSDT",
            "exchange": "binance",
            "event_time": "2026-02-14T10:00:00Z",
            "price": 3000.0,
            "quantity": 0.5,
            "side": "sell",
            "trade_id": "tick-01",
        }
    )
    assert tick.schema_version == "1.0"
    assert len(store.ticks) == 1


def test_data_store_next_id_rejects_unknown_scope() -> None:
    store = InMemoryDataStore()
    with pytest.raises(ValueError):
        store.next_id("unknown")
