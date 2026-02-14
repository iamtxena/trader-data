"""Deterministic filter/transform engine for candles."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from trader_data.models.market_data import CandleV1


def _deterministic_hash(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CandleTransformResult:
    item_count: int
    output_hash: str
    items: list[dict[str, object]]


class TransformEngine:
    """Applies reproducible filter/transform operations."""

    def transform_candles(
        self,
        *,
        candles: list[CandleV1],
        min_volume: float = 0.0,
    ) -> CandleTransformResult:
        ordered = sorted(
            candles,
            key=lambda item: (
                item.symbol,
                item.exchange,
                item.interval,
                item.event_time.isoformat(),
                item.open,
                item.high,
                item.low,
                item.close,
                item.volume,
            ),
        )

        transformed: list[dict[str, object]] = []
        by_series: dict[tuple[str, str, str], float] = {}
        for candle in ordered:
            key = (candle.symbol, candle.exchange, candle.interval)
            previous_close = by_series.get(key)
            close_return = 0.0 if previous_close is None or previous_close == 0 else (candle.close - previous_close) / previous_close
            by_series[key] = candle.close
            if candle.volume < min_volume:
                continue
            transformed.append(
                {
                    "schemaVersion": candle.schema_version,
                    "symbol": candle.symbol,
                    "exchange": candle.exchange,
                    "interval": candle.interval,
                    "eventTime": candle.event_time.isoformat().replace("+00:00", "Z"),
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                    "closeReturn": round(close_return, 10),
                }
            )

        output_hash = _deterministic_hash(
            {
                "minVolume": min_volume,
                "items": transformed,
            }
        )
        return CandleTransformResult(item_count=len(transformed), output_hash=output_hash, items=transformed)
