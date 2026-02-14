"""Canonical market data model for Gate3 DATA-02."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import Any, Mapping

MARKET_DATA_SCHEMA_VERSION = "1.0"


def _as_str(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _as_float(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric.")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{field_name} must be finite.")
    return converted


def _as_timestamp(value: object, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp string.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO-8601 timestamp.") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone information.")
    return parsed.astimezone(timezone.utc)


def _validate_schema(payload: Mapping[str, object]) -> None:
    schema_version = payload.get("schema_version")
    if schema_version != MARKET_DATA_SCHEMA_VERSION:
        raise ValueError(f"Unsupported schema_version; expected '{MARKET_DATA_SCHEMA_VERSION}'.")


@dataclass(frozen=True)
class TickV1:
    schema_version: str
    symbol: str
    exchange: str
    event_time: datetime
    price: float
    quantity: float
    side: str
    trade_id: str

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "TickV1":
        _validate_schema(payload)
        side = _as_str(payload["side"], "side").lower()
        if side not in {"buy", "sell"}:
            raise ValueError("side must be 'buy' or 'sell'.")
        price = _as_float(payload["price"], "price")
        quantity = _as_float(payload["quantity"], "quantity")
        if price <= 0:
            raise ValueError("price must be > 0.")
        if quantity <= 0:
            raise ValueError("quantity must be > 0.")
        return cls(
            schema_version=MARKET_DATA_SCHEMA_VERSION,
            symbol=_as_str(payload["symbol"], "symbol").upper(),
            exchange=_as_str(payload["exchange"], "exchange").lower(),
            event_time=_as_timestamp(payload["event_time"], "event_time"),
            price=price,
            quantity=quantity,
            side=side,
            trade_id=_as_str(payload["trade_id"], "trade_id"),
        )


@dataclass(frozen=True)
class OrderBookLevelV1:
    price: float
    quantity: float


@dataclass(frozen=True)
class OrderBookSnapshotV1:
    schema_version: str
    symbol: str
    exchange: str
    event_time: datetime
    bids: list[OrderBookLevelV1] = field(default_factory=list)
    asks: list[OrderBookLevelV1] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "OrderBookSnapshotV1":
        _validate_schema(payload)
        bids = _parse_levels(payload.get("bids"), "bids")
        asks = _parse_levels(payload.get("asks"), "asks")
        if not bids and not asks:
            raise ValueError("at least one of bids/asks must be provided.")
        return cls(
            schema_version=MARKET_DATA_SCHEMA_VERSION,
            symbol=_as_str(payload["symbol"], "symbol").upper(),
            exchange=_as_str(payload["exchange"], "exchange").lower(),
            event_time=_as_timestamp(payload["event_time"], "event_time"),
            bids=bids,
            asks=asks,
        )


@dataclass(frozen=True)
class CandleV1:
    schema_version: str
    symbol: str
    exchange: str
    interval: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    event_time: datetime

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "CandleV1":
        _validate_schema(payload)
        open_price = _as_float(payload["open"], "open")
        high_price = _as_float(payload["high"], "high")
        low_price = _as_float(payload["low"], "low")
        close_price = _as_float(payload["close"], "close")
        volume = _as_float(payload["volume"], "volume")
        if min(open_price, high_price, low_price, close_price) <= 0:
            raise ValueError("OHLC values must be > 0.")
        if high_price < low_price:
            raise ValueError("high must be >= low.")
        if not (low_price <= open_price <= high_price):
            raise ValueError("open must be within [low, high].")
        if not (low_price <= close_price <= high_price):
            raise ValueError("close must be within [low, high].")
        if volume < 0:
            raise ValueError("volume must be >= 0.")
        return cls(
            schema_version=MARKET_DATA_SCHEMA_VERSION,
            symbol=_as_str(payload["symbol"], "symbol").upper(),
            exchange=_as_str(payload["exchange"], "exchange").lower(),
            interval=_as_str(payload["interval"], "interval"),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
            event_time=_as_timestamp(payload["event_time"], "event_time"),
        )


@dataclass(frozen=True)
class ContextualCandleV1:
    schema_version: str
    candle: CandleV1
    sentiment: float
    regime: str | None = None
    news: list[dict[str, Any]] = field(default_factory=list)
    custom: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "ContextualCandleV1":
        _validate_schema(payload)
        candle_payload = payload.get("candle")
        if not isinstance(candle_payload, Mapping):
            raise ValueError("candle must be an object payload.")
        sentiment = _as_float(payload.get("sentiment", 0.0), "sentiment")
        if sentiment < -1 or sentiment > 1:
            raise ValueError("sentiment must be between -1 and 1.")
        news_payload = payload.get("news", [])
        if not isinstance(news_payload, list):
            raise ValueError("news must be a list.")
        custom_payload = payload.get("custom", {})
        if not isinstance(custom_payload, Mapping):
            raise ValueError("custom must be a key-value object.")
        custom: dict[str, float] = {str(key): _as_float(value, f"custom[{key}]") for key, value in custom_payload.items()}

        news: list[dict[str, Any]] = []
        for index, item in enumerate(news_payload):
            if not isinstance(item, Mapping):
                raise ValueError(f"news[{index}] must be an object.")
            news.append(dict(item))

        return cls(
            schema_version=MARKET_DATA_SCHEMA_VERSION,
            candle=CandleV1.from_payload(candle_payload),
            sentiment=sentiment,
            regime=_as_str(payload["regime"], "regime") if payload.get("regime") is not None else None,
            news=news,
            custom=custom,
        )


def _parse_levels(value: object, field_name: str) -> list[OrderBookLevelV1]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list.")

    levels: list[OrderBookLevelV1] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(f"{field_name}[{index}] must be an object.")
        price = _as_float(item.get("price"), f"{field_name}[{index}].price")
        quantity = _as_float(item.get("quantity"), f"{field_name}[{index}].quantity")
        if price <= 0 or quantity <= 0:
            raise ValueError(f"{field_name}[{index}] has invalid price/quantity.")
        levels.append(OrderBookLevelV1(price=price, quantity=quantity))
    return levels
