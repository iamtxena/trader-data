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
    def fetch_market_context(self, *, symbol: str, context: ProviderContext) -> dict:
        """Retrieve normalized market context for internal platform use."""

