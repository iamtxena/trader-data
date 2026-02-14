"""In-memory persistence primitives for Gate3 internal data services."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from trader_data.models.market_data import CandleV1, ContextualCandleV1, OrderBookSnapshotV1, TickV1


def utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class DataExportRecord:
    id: str
    status: str
    dataset_ids: list[str]
    asset_classes: list[str]
    download_url: str | None
    lineage: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


class InMemoryDataStore:
    """Storage for internal ingestion/transform/export workflows."""

    def __init__(self) -> None:
        self.ticks: list[TickV1] = []
        self.orderbooks: list[OrderBookSnapshotV1] = []
        self.candles: list[CandleV1] = []
        self.contextual_candles: list[ContextualCandleV1] = []
        self.exports: dict[str, DataExportRecord] = {}
        self._id_counters: dict[str, int] = {
            "export": 1,
        }

    def next_id(self, scope: str) -> str:
        if scope != "export":
            raise ValueError(f"Unsupported id scope: {scope}")
        idx = self._id_counters[scope]
        self._id_counters[scope] = idx + 1
        return f"exp-{idx:04d}"
