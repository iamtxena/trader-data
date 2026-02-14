"""Provider adapter contract for trader-data.

Gate0 intentionally defines boundary contracts only. No public endpoint
implementation is introduced in this bootstrap.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderContext:
    tenant_id: str
    user_id: str
    request_id: str


class ProviderAdapter(Protocol):
    def fetch_ticks(self, *, symbol: str, limit: int, context: ProviderContext) -> list[dict]:
        """Retrieve normalized trade ticks for the requested symbol."""

    def fetch_orderbook(self, *, symbol: str, depth: int, context: ProviderContext) -> dict:
        """Retrieve normalized orderbook snapshot."""

    def fetch_candles(
        self,
        *,
        symbol: str,
        interval: str,
        start_time: str | None,
        end_time: str | None,
        context: ProviderContext,
    ) -> list[dict]:
        """Retrieve normalized OHLCV candles for backfill windows."""

    def fetch_market_context(self, *, symbol: str, context: ProviderContext) -> dict:
        """Retrieve normalized market context for internal platform use."""
