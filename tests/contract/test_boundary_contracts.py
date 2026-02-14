"""Gate0 boundary tests for trader-data bootstrap."""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
CONTRACT_DOC = REPO_ROOT / "contracts/platform-api-entrypoint.md"
ADAPTER_INTERFACE = REPO_ROOT / "src/trader_data/adapters/provider_interface.py"


def test_contract_doc_exists_and_points_to_platform_api() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    assert "No external client endpoint is exposed from this repository." in text
    assert "Internal routes are restricted to `/internal/v1/*`" in text
    assert "All external client traffic must enter through Platform API" in text
    assert "platform-api.openapi.yaml" in text


def test_provider_interface_is_adapter_scoped() -> None:
    text = ADAPTER_INTERFACE.read_text(encoding="utf-8")
    assert "class ProviderAdapter(Protocol)" in text
    assert "fetch_ticks" in text
    assert "fetch_orderbook" in text
    assert "fetch_candles" in text
    assert "fetch_market_context" in text
    assert "tenant_id" in text
    assert "user_id" in text
    assert "request_id" in text


def test_internal_api_routes_stay_internal_only() -> None:
    python_files = SRC_ROOT.rglob("*.py")
    route_pattern = re.compile(
        r"@(?:app|router)\.(?:get|post|put|patch|delete)\(\s*(?P<quote>['\"])(?P<path>[^'\"]+)(?P=quote)\s*\)"
    )

    for file_path in python_files:
        text = file_path.read_text(encoding="utf-8")
        for match in route_pattern.finditer(text):
            path = match.group("path")
            assert path.startswith("/internal/v1/"), f"Route must stay internal-only: {path} in {file_path}"


def test_internal_api_route_regex_matches_single_and_double_quotes() -> None:
    route_pattern = re.compile(
        r"@(?:app|router)\.(?:get|post|put|patch|delete)\(\s*(?P<quote>['\"])(?P<path>[^'\"]+)(?P=quote)\s*\)"
    )
    assert route_pattern.search("@app.get('/internal/v1/ping')")
    assert route_pattern.search('@router.post("/internal/v1/exports/backtest")')
