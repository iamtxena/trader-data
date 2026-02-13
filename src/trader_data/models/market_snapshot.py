"""Canonical market snapshot schema and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


@dataclass(frozen=True)
class MarketSnapshotV1:
    """Normalized market snapshot payload for internal platform data flows."""

    schema_version: str
    symbol: str
    event_time: datetime
    ingest_time: datetime
    price: float
    volume: float
    source: str

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "MarketSnapshotV1":
        required_keys = (
            "schema_version",
            "symbol",
            "event_time",
            "ingest_time",
            "price",
            "volume",
            "source",
        )

        missing = [key for key in required_keys if key not in payload]
        if missing:
            raise ValueError(f"Missing required keys: {', '.join(missing)}")

        schema_version = _as_str(payload["schema_version"], "schema_version")
        if schema_version != "1.0":
            raise ValueError("Unsupported schema_version; expected '1.0'.")

        symbol = _as_str(payload["symbol"], "symbol").upper()
        source = _as_str(payload["source"], "source")

        event_time = _as_utc_timestamp(payload["event_time"], "event_time")
        ingest_time = _as_utc_timestamp(payload["ingest_time"], "ingest_time")
        if ingest_time < event_time:
            raise ValueError("ingest_time must be greater than or equal to event_time.")

        price = _as_float(payload["price"], "price")
        if price <= 0:
            raise ValueError("price must be greater than zero.")

        volume = _as_float(payload["volume"], "volume")
        if volume < 0:
            raise ValueError("volume must be greater than or equal to zero.")

        return cls(
            schema_version=schema_version,
            symbol=symbol,
            event_time=event_time,
            ingest_time=ingest_time,
            price=price,
            volume=volume,
            source=source,
        )


def _as_str(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _as_float(value: object, field_name: str) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric.")
    return float(value)


def _as_utc_timestamp(value: object, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp string.")

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO-8601 timestamp.") from exc

    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone information.")

    return parsed.astimezone(timezone.utc)
