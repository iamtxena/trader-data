"""Internal authenticated API for trader-data service-to-service calls."""

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from trader_data.services import InternalDataService, RequestIdentity
from trader_data.store import InMemoryDataStore

app = FastAPI(title="trader-data internal api", version="0.1.0")
_store = InMemoryDataStore()
_service = InternalDataService(_store)


def _expected_service_key() -> str | None:
    return os.getenv("TRADER_DATA_SERVICE_API_KEY") or os.getenv("SERVICE_API_KEY")


def _require_service_auth(authorization: str | None = Header(default=None, alias="Authorization")) -> None:
    expected = _expected_service_key()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service authentication key is not configured.",
        )
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized service caller.")


def _identity(
    request: Request,
    _: None = Depends(_require_service_auth),
    x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> RequestIdentity:
    request_id = x_request_id or f"req-{uuid4()}"
    request.state.request_id = request_id
    return RequestIdentity(
        request_id=request_id,
        tenant_id=x_tenant_id or "tenant-local",
        user_id=x_user_id or "service-account",
    )


class TickIngestionRequest(BaseModel):
    symbol: str
    exchange: str
    event_time: str
    price: float
    quantity: float
    side: str
    trade_id: str
    schema_version: str = "1.0"


class OrderBookLevelRequest(BaseModel):
    price: float
    quantity: float


class OrderBookIngestionRequest(BaseModel):
    symbol: str
    exchange: str
    event_time: str
    bids: list[OrderBookLevelRequest] = Field(default_factory=list)
    asks: list[OrderBookLevelRequest] = Field(default_factory=list)
    schema_version: str = "1.0"


class CandleIngestionRequest(BaseModel):
    symbol: str
    exchange: str
    interval: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    event_time: str
    schema_version: str = "1.0"


class CandleBackfillRequest(BaseModel):
    candles: list[CandleIngestionRequest] = Field(min_length=1)


class CandleTransformRequest(BaseModel):
    symbol: str | None = None
    interval: str | None = None
    minVolume: float = Field(default=0.0, ge=0.0)


class BacktestExportRequest(BaseModel):
    datasetIds: list[str] = Field(min_length=1)
    assetClasses: list[str] = Field(default_factory=list)


class MarketContextRequest(BaseModel):
    assetClasses: list[str] = Field(default_factory=list)


@app.post("/internal/v1/ingestion/ticks")
def ingest_tick(payload: TickIngestionRequest, identity: RequestIdentity = Depends(_identity)) -> dict[str, Any]:
    _ = identity
    tick = _service.ingestion.ingest_tick(payload.model_dump())
    return {
        "schemaVersion": tick.schema_version,
        "symbol": tick.symbol,
        "exchange": tick.exchange,
        "eventTime": tick.event_time.isoformat().replace("+00:00", "Z"),
        "price": tick.price,
        "quantity": tick.quantity,
        "side": tick.side,
        "tradeId": tick.trade_id,
    }


@app.post("/internal/v1/ingestion/orderbook")
def ingest_orderbook(
    payload: OrderBookIngestionRequest,
    identity: RequestIdentity = Depends(_identity),
) -> dict[str, object]:
    _ = identity
    snapshot = _service.ingestion.ingest_orderbook(payload.model_dump())
    return {
        "schemaVersion": snapshot.schema_version,
        "symbol": snapshot.symbol,
        "exchange": snapshot.exchange,
        "eventTime": snapshot.event_time.isoformat().replace("+00:00", "Z"),
        "bids": [{"price": level.price, "quantity": level.quantity} for level in snapshot.bids],
        "asks": [{"price": level.price, "quantity": level.quantity} for level in snapshot.asks],
    }


@app.post("/internal/v1/ingestion/candles")
def ingest_candle(payload: CandleIngestionRequest, identity: RequestIdentity = Depends(_identity)) -> dict[str, object]:
    _ = identity
    candle = _service.ingestion.ingest_candle(payload.model_dump())
    return {
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
    }


@app.post("/internal/v1/ingestion/backfill/candles")
def backfill_candles(
    payload: CandleBackfillRequest,
    identity: RequestIdentity = Depends(_identity),
) -> dict[str, object]:
    _ = identity
    candles = _service.ingestion.backfill_candles(item.model_dump() for item in payload.candles)
    return {
        "ingestedCount": len(candles),
        "items": [
            {
                "symbol": item.symbol,
                "interval": item.interval,
                "eventTime": item.event_time.isoformat().replace("+00:00", "Z"),
            }
            for item in candles
        ],
    }


@app.post("/internal/v1/transforms/candles")
def transform_candles(
    payload: CandleTransformRequest,
    identity: RequestIdentity = Depends(_identity),
) -> dict[str, object]:
    _ = identity
    return _service.transform_candles(
        symbol=payload.symbol,
        interval=payload.interval,
        min_volume=payload.minVolume,
    )


@app.post("/internal/v1/exports/backtest")
def create_backtest_export(
    payload: BacktestExportRequest,
    identity: RequestIdentity = Depends(_identity),
) -> dict[str, object]:
    return _service.create_backtest_export(
        dataset_ids=payload.datasetIds,
        asset_classes=payload.assetClasses,
        identity=identity,
    )


@app.get("/internal/v1/exports/{export_id}")
def get_backtest_export(
    export_id: str,
    identity: RequestIdentity = Depends(_identity),
) -> dict[str, object]:
    _ = identity
    export = _service.get_backtest_export(export_id=export_id)
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Export {export_id} not found.")
    return export


@app.post("/internal/v1/context/market")
def get_market_context(
    payload: MarketContextRequest,
    identity: RequestIdentity = Depends(_identity),
) -> dict[str, object]:
    _ = identity
    return _service.get_market_context(asset_classes=payload.assetClasses)
