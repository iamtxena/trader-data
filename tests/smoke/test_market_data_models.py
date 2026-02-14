"""Smoke tests for Gate3 canonical market data models."""

from datetime import timezone

import pytest

from trader_data.models.market_data import CandleV1, ContextualCandleV1, OrderBookSnapshotV1, TickV1


def test_tick_v1_accepts_valid_payload() -> None:
    payload = {
        "schema_version": "1.0",
        "symbol": "btcusdt",
        "exchange": "binance",
        "event_time": "2026-02-14T12:00:00Z",
        "price": 102000.1,
        "quantity": 0.2,
        "side": "buy",
        "trade_id": "t-001",
    }
    tick = TickV1.from_payload(payload)
    assert tick.symbol == "BTCUSDT"
    assert tick.event_time.tzinfo == timezone.utc
    assert tick.price == pytest.approx(102000.1)


def test_orderbook_requires_levels() -> None:
    payload = {
        "schema_version": "1.0",
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "event_time": "2026-02-14T12:00:00Z",
        "bids": [],
        "asks": [],
    }
    with pytest.raises(ValueError):
        OrderBookSnapshotV1.from_payload(payload)


def test_orderbook_rejects_zero_quantity_levels() -> None:
    payload = {
        "schema_version": "1.0",
        "symbol": "BTCUSDT",
        "exchange": "binance",
        "event_time": "2026-02-14T12:00:00Z",
        "bids": [{"price": 64000.0, "quantity": 0}],
    }
    with pytest.raises(ValueError):
        OrderBookSnapshotV1.from_payload(payload)


def test_candle_validates_ohlc_relationships() -> None:
    payload = {
        "schema_version": "1.0",
        "symbol": "ETHUSDT",
        "exchange": "binance",
        "interval": "1m",
        "open": 2750.0,
        "high": 2700.0,
        "low": 2740.0,
        "close": 2760.0,
        "volume": 50.0,
        "event_time": "2026-02-14T12:00:00Z",
    }
    with pytest.raises(ValueError):
        CandleV1.from_payload(payload)


def test_candle_requires_open_close_within_low_high_bounds() -> None:
    payload = {
        "schema_version": "1.0",
        "symbol": "ETHUSDT",
        "exchange": "binance",
        "interval": "1m",
        "open": 2750.0,
        "high": 2740.0,
        "low": 2740.0,
        "close": 2730.0,
        "volume": 50.0,
        "event_time": "2026-02-14T12:00:00Z",
    }
    with pytest.raises(ValueError):
        CandleV1.from_payload(payload)


def test_contextual_candle_validates_sentiment() -> None:
    payload = {
        "schema_version": "1.0",
        "sentiment": 1.2,
        "candle": {
            "schema_version": "1.0",
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "interval": "5m",
            "open": 101000.0,
            "high": 101500.0,
            "low": 100900.0,
            "close": 101200.0,
            "volume": 10.0,
            "event_time": "2026-02-14T12:00:00Z",
        },
    }
    with pytest.raises(ValueError):
        ContextualCandleV1.from_payload(payload)


def test_contextual_candle_rejects_non_object_news_entries() -> None:
    payload = {
        "schema_version": "1.0",
        "sentiment": 0.4,
        "news": [{"headline": "CPI cools"}, "bad-entry"],
        "candle": {
            "schema_version": "1.0",
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "interval": "5m",
            "open": 101000.0,
            "high": 101500.0,
            "low": 100900.0,
            "close": 101200.0,
            "volume": 10.0,
            "event_time": "2026-02-14T12:00:00Z",
        },
    }
    with pytest.raises(ValueError):
        ContextualCandleV1.from_payload(payload)
