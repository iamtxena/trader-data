"""Provider boundary tests for trader-data."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_INTERFACE = REPO_ROOT / "src/trader_data/adapters/provider_interface.py"


def test_provider_interface_keeps_adapter_protocol_boundary() -> None:
    text = ADAPTER_INTERFACE.read_text(encoding="utf-8")
    assert "class ProviderAdapter(Protocol)" in text
    assert "fetch_market_context" in text


def test_provider_interface_avoids_direct_transport_dependencies() -> None:
    text = ADAPTER_INTERFACE.read_text(encoding="utf-8")
    disallowed_markers = ("requests", "httpx", "aiohttp", "ccxt")
    for marker in disallowed_markers:
        assert marker not in text, f"Provider interface should stay transport-agnostic: {marker}"
