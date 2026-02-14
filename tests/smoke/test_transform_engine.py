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


def test_transform_engine_keeps_exchange_series_isolated() -> None:
    store = InMemoryDataStore()
    ingestion = IngestionPipeline(store)
    engine = TransformEngine()

    payloads = [
        {
            "schema_version": "1.0",
            "symbol": "BTCUSDT",
            "exchange": "coinbase",
            "interval": "1m",
            "open": 200.0,
            "high": 201.0,
            "low": 199.0,
            "close": 200.0,
            "volume": 5.0,
            "event_time": "2026-02-14T10:00:00Z",
        },
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
            "exchange": "coinbase",
            "interval": "1m",
            "open": 200.0,
            "high": 221.0,
            "low": 199.0,
            "close": 220.0,
            "volume": 5.0,
            "event_time": "2026-02-14T10:01:00Z",
        },
        {
            "schema_version": "1.0",
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "interval": "1m",
            "open": 100.0,
            "high": 111.0,
            "low": 99.0,
            "close": 110.0,
            "volume": 5.0,
            "event_time": "2026-02-14T10:01:00Z",
        },
    ]
    for payload in payloads:
        ingestion.ingest_candle(payload)

    transformed = engine.transform_candles(candles=list(store.candles), min_volume=0.0).items
    returns_by_exchange: dict[str, list[float]] = {}
    for item in transformed:
        exchange = str(item["exchange"])
        returns_by_exchange.setdefault(exchange, []).append(float(item["closeReturn"]))

    assert returns_by_exchange["binance"] == [0.0, 0.1]
    assert returns_by_exchange["coinbase"] == [0.0, 0.1]


def test_transform_engine_close_return_uses_full_series_before_filtering() -> None:
    store = InMemoryDataStore()
    ingestion = IngestionPipeline(store)
    engine = TransformEngine()

    for payload in [
        {
            "schema_version": "1.0",
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "interval": "1m",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 2.0,
            "event_time": "2026-02-14T10:00:00Z",
        },
        {
            "schema_version": "1.0",
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "interval": "1m",
            "open": 100.0,
            "high": 111.0,
            "low": 99.0,
            "close": 110.0,
            "volume": 0.5,
            "event_time": "2026-02-14T10:01:00Z",
        },
        {
            "schema_version": "1.0",
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "interval": "1m",
            "open": 110.0,
            "high": 123.0,
            "low": 109.0,
            "close": 121.0,
            "volume": 2.0,
            "event_time": "2026-02-14T10:02:00Z",
        },
    ]:
        ingestion.ingest_candle(payload)

    items = engine.transform_candles(candles=list(store.candles), min_volume=1.0).items
    assert [float(item["closeReturn"]) for item in items] == [0.0, 0.1]


def test_transform_engine_sorting_is_deterministic_for_duplicate_timestamps() -> None:
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
            "high": 103.0,
            "low": 99.0,
            "close": 102.0,
            "volume": 5.0,
            "event_time": "2026-02-14T10:00:00Z",
        },
    ]
    for payload in payloads:
        ingestion.ingest_candle(payload)

    first = engine.transform_candles(candles=list(store.candles), min_volume=0.0)
    second = engine.transform_candles(candles=list(reversed(store.candles)), min_volume=0.0)
    assert first.items == second.items
    assert first.output_hash == second.output_hash
