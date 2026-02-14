"""Smoke tests for internal data service filtering/export/context behavior."""

from trader_data.models.market_data import CandleV1
from trader_data.services.internal_data_service import InternalDataService, RequestIdentity
from trader_data.store import InMemoryDataStore


def _identity() -> RequestIdentity:
    return RequestIdentity(request_id="req-1", tenant_id="tenant-a", user_id="user-a")


def _candle(symbol: str, close: float, event_time: str) -> CandleV1:
    return CandleV1.from_payload(
        {
            "schema_version": "1.0",
            "symbol": symbol,
            "exchange": "binance",
            "interval": "1m",
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 10.0,
            "event_time": event_time,
        }
    )


def test_create_backtest_export_uses_configurable_download_base_url() -> None:
    store = InMemoryDataStore()
    store.candles.append(_candle("BTCUSDT", 100.0, "2026-02-14T10:00:00Z"))
    service = InternalDataService(store, export_base_url="https://data.internal.local/")

    created = service.create_backtest_export(
        dataset_ids=["dataset-1"],
        asset_classes=["crypto"],
        identity=_identity(),
    )

    assert created["downloadUrl"] == "https://data.internal.local/exports/exp-0001.parquet"


def test_asset_class_filter_keeps_fx_and_crypto_distinct() -> None:
    store = InMemoryDataStore()
    store.candles.extend(
        [
            _candle("BTCUSD", 100.0, "2026-02-14T10:00:00Z"),
            _candle("EURUSD", 1.1, "2026-02-14T10:01:00Z"),
            _candle("AAPL", 180.0, "2026-02-14T10:02:00Z"),
        ]
    )
    service = InternalDataService(store)

    crypto_symbols = [item.symbol for item in service._filter_candles_for_asset_classes(["crypto"])]
    fx_symbols = [item.symbol for item in service._filter_candles_for_asset_classes(["fx"])]
    equity_symbols = [item.symbol for item in service._filter_candles_for_asset_classes(["equity"])]

    assert crypto_symbols == ["BTCUSD"]
    assert fx_symbols == ["EURUSD"]
    assert equity_symbols == ["AAPL"]


def test_market_context_uses_latest_series_for_volatility() -> None:
    store = InMemoryDataStore()
    store.candles.extend(
        [
            _candle("ETHUSDT", 100.0, "2026-02-14T10:00:00Z"),
            _candle("ETHUSDT", 150.0, "2026-02-14T10:01:00Z"),
            _candle("BTCUSDT", 200.0, "2026-02-14T10:02:00Z"),
            _candle("BTCUSDT", 201.0, "2026-02-14T10:03:00Z"),
        ]
    )
    service = InternalDataService(store)

    context = service.get_market_context(asset_classes=["crypto"])

    assert context["regimeSummary"] == "BTCUSDT 1m regime indicates low volatility."
    sample_size_signal = next(item for item in context["signals"] if item["name"] == "sample_size")
    assert sample_size_signal["value"] == "2"
