"""Canonical ingestion pipelines for ticks/orderbooks/candles."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from trader_data.models.market_data import (
    MARKET_DATA_SCHEMA_VERSION,
    CandleV1,
    OrderBookSnapshotV1,
    TickV1,
)
from trader_data.store import InMemoryDataStore


def _with_default_schema(payload: Mapping[str, object]) -> dict[str, object]:
    normalized = dict(payload)
    normalized.setdefault("schema_version", MARKET_DATA_SCHEMA_VERSION)
    return normalized


class IngestionPipeline:
    """Validates and stores canonical market data records."""

    def __init__(self, store: InMemoryDataStore) -> None:
        self._store = store

    def ingest_tick(self, payload: Mapping[str, object]) -> TickV1:
        tick = TickV1.from_payload(_with_default_schema(payload))
        self._store.ticks.append(tick)
        return tick

    def ingest_orderbook(self, payload: Mapping[str, object]) -> OrderBookSnapshotV1:
        snapshot = OrderBookSnapshotV1.from_payload(_with_default_schema(payload))
        self._store.orderbooks.append(snapshot)
        return snapshot

    def ingest_candle(self, payload: Mapping[str, object]) -> CandleV1:
        candle = CandleV1.from_payload(_with_default_schema(payload))
        self._store.candles.append(candle)
        return candle

    def backfill_candles(self, payloads: Iterable[Mapping[str, object]]) -> list[CandleV1]:
        candles = [CandleV1.from_payload(_with_default_schema(item)) for item in payloads]
        candles.sort(key=lambda candle: (candle.symbol, candle.exchange, candle.interval, candle.event_time))
        self._store.candles.extend(candles)
        return candles
