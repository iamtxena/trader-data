"""Gate0 boundary tests for trader-data bootstrap."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
CONTRACT_DOC = REPO_ROOT / "contracts/platform-api-entrypoint.md"
ADAPTER_INTERFACE = REPO_ROOT / "src/trader_data/adapters/provider_interface.py"


def test_contract_doc_exists_and_points_to_platform_api() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    assert "No public endpoint is defined in this repository during Gate0." in text
    assert "All external client traffic must enter through Platform API" in text
    assert "platform-api.openapi.yaml" in text


def test_provider_interface_is_adapter_scoped() -> None:
    text = ADAPTER_INTERFACE.read_text(encoding="utf-8")
    assert "class ProviderAdapter(Protocol)" in text
    assert "fetch_market_context" in text
    assert "tenant_id" in text
    assert "user_id" in text
    assert "request_id" in text


def test_no_public_api_endpoint_implementation_in_gate0() -> None:
    python_files = SRC_ROOT.rglob("*.py")
    disallowed_markers = ("FastAPI(", "@app.get(", "@app.post(", "@router.get(", "@router.post(")

    for file_path in python_files:
        text = file_path.read_text(encoding="utf-8")
        assert not any(marker in text for marker in disallowed_markers), (
            f"Gate0 bootstrap must stay endpoint-free; found API marker in {file_path}."
        )
