"""Service layer backing trader-data internal routes."""

from __future__ import annotations

from dataclasses import dataclass

from trader_data.ingestion.pipeline import IngestionPipeline
from trader_data.models.market_data import CandleV1
from trader_data.store import DataExportRecord, InMemoryDataStore, utc_now
from trader_data.transforms.engine import TransformEngine


@dataclass(frozen=True)
class RequestIdentity:
    tenant_id: str
    user_id: str
    request_id: str


class InternalDataService:
    """Coordinates ingestion, transforms, and export/context creation."""

    def __init__(self, store: InMemoryDataStore) -> None:
        self._store = store
        self._ingestion = IngestionPipeline(store)
        self._transforms = TransformEngine()

    @property
    def ingestion(self) -> IngestionPipeline:
        return self._ingestion

    def transform_candles(self, *, symbol: str | None, interval: str | None, min_volume: float) -> dict[str, object]:
        candles = self._store.candles
        if symbol:
            candles = [item for item in candles if item.symbol == symbol.upper()]
        if interval:
            candles = [item for item in candles if item.interval == interval]
        result = self._transforms.transform_candles(candles=candles, min_volume=min_volume)
        return {
            "itemCount": result.item_count,
            "outputHash": result.output_hash,
            "items": result.items,
        }

    def create_backtest_export(
        self,
        *,
        dataset_ids: list[str],
        asset_classes: list[str],
        identity: RequestIdentity,
    ) -> dict[str, object]:
        export_id = self._store.next_id("export")
        candles = self._filter_candles_for_asset_classes(asset_classes)
        transform_result = self._transforms.transform_candles(candles=candles, min_volume=0.0)
        now = utc_now()
        record = DataExportRecord(
            id=export_id,
            status="completed",
            dataset_ids=list(dataset_ids),
            asset_classes=list(asset_classes),
            download_url=f"https://trader-data.internal/exports/{export_id}.parquet",
            lineage={
                "tenantId": identity.tenant_id,
                "requestId": identity.request_id,
                "datasetCount": len(dataset_ids),
                "assetClasses": sorted({entry.lower() for entry in asset_classes}),
                "transformHash": transform_result.output_hash,
                "generatedAt": now,
            },
            created_at=now,
            updated_at=now,
        )
        self._store.exports[record.id] = record
        return _serialize_export(record)

    def get_backtest_export(self, *, export_id: str) -> dict[str, object] | None:
        record = self._store.exports.get(export_id)
        if record is None:
            return None
        return _serialize_export(record)

    def get_market_context(self, *, asset_classes: list[str]) -> dict[str, object]:
        candles = self._filter_candles_for_asset_classes(asset_classes)
        if not candles:
            return {
                "regimeSummary": "Context unavailable for requested assets.",
                "signals": [],
                "generatedAt": utc_now(),
            }

        latest = sorted(candles, key=lambda item: item.event_time.isoformat())[-1]
        volatility = _volatility_label(candles)
        return {
            "regimeSummary": f"{latest.symbol} {latest.interval} regime indicates {volatility} volatility.",
            "signals": [
                {"name": "volatility", "value": volatility},
                {"name": "latest_close", "value": f"{latest.close:.6f}"},
                {"name": "sample_size", "value": str(len(candles))},
            ],
            "generatedAt": utc_now(),
        }

    def _filter_candles_for_asset_classes(self, asset_classes: list[str]) -> list[CandleV1]:
        normalized = {entry.lower() for entry in asset_classes}
        if not normalized:
            return list(self._store.candles)

        def include(candle: CandleV1) -> bool:
            symbol = candle.symbol.upper()
            if "crypto" in normalized and symbol.endswith(("USDT", "USD")):
                return True
            if "fx" in normalized and symbol.endswith("USD") and len(symbol) == 6:
                return True
            if "equity" in normalized and not symbol.endswith(("USDT", "USD")):
                return True
            return False

        return [item for item in self._store.candles if include(item)]


def _serialize_export(record: DataExportRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "status": record.status,
        "datasetIds": record.dataset_ids,
        "assetClasses": record.asset_classes,
        "downloadUrl": record.download_url,
        "lineage": record.lineage,
        "createdAt": record.created_at,
        "updatedAt": record.updated_at,
    }


def _volatility_label(candles: list[CandleV1]) -> str:
    if len(candles) < 2:
        return "unknown"
    returns: list[float] = []
    previous = candles[0].close
    for candle in candles[1:]:
        if previous > 0:
            returns.append(abs((candle.close - previous) / previous))
        previous = candle.close
    if not returns:
        return "unknown"
    average = sum(returns) / len(returns)
    if average >= 0.03:
        return "high"
    if average >= 0.01:
        return "medium"
    return "low"
