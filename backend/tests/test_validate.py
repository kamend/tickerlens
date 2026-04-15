import pytest
from fastapi.testclient import TestClient

import clients.yfinance_client as yf_client
from clients.yfinance_client import TickerNotFoundError, fetch_info
from graph.nodes.validate import validate_ticker_node
from main import app


pytestmark = pytest.mark.no_mock_yfinance


class _FakeTicker:
    def __init__(self, info):
        self.info = info

    def get_info(self):
        return self.info


def _patch_ticker(monkeypatch, info_by_symbol):
    def _factory(symbol):
        return _FakeTicker(info_by_symbol.get(symbol.upper(), {}))

    monkeypatch.setattr(yf_client.yfinance, "Ticker", _factory)


def test_fetch_info_returns_dict_for_valid_ticker(monkeypatch):
    _patch_ticker(monkeypatch, {"AAPL": {"longName": "Apple Inc.", "symbol": "AAPL"}})
    info = fetch_info("AAPL")
    assert info["longName"] == "Apple Inc."


def test_fetch_info_raises_for_missing_long_name(monkeypatch):
    _patch_ticker(monkeypatch, {"ZZZZZ": {"symbol": "ZZZZZ"}})
    with pytest.raises(TickerNotFoundError):
        fetch_info("ZZZZZ")


def test_fetch_info_raises_for_empty_info(monkeypatch):
    _patch_ticker(monkeypatch, {"ZZZZZ": {}})
    with pytest.raises(TickerNotFoundError):
        fetch_info("ZZZZZ")


def test_fetch_info_raises_for_empty_string(monkeypatch):
    _patch_ticker(monkeypatch, {})
    with pytest.raises(TickerNotFoundError):
        fetch_info("")


def test_fetch_info_normalizes_case_and_whitespace(monkeypatch):
    _patch_ticker(monkeypatch, {"AAPL": {"longName": "Apple Inc."}})
    assert fetch_info("  aapl ")["longName"] == "Apple Inc."


async def test_validate_node_valid_ticker(monkeypatch):
    _patch_ticker(monkeypatch, {"AAPL": {"longName": "Apple Inc."}})
    # The node imports fetch_info at module load; monkeypatch the reference it uses.
    import graph.nodes.validate as v
    monkeypatch.setattr(v, "fetch_info", fetch_info)

    result = await validate_ticker_node({"ticker": "AAPL"})
    assert result["company_name"] == "Apple Inc."
    assert result["validation_error"] is None
    assert "AAPL" in result["status_message"]


async def test_validate_node_invalid_ticker(monkeypatch):
    _patch_ticker(monkeypatch, {})
    import graph.nodes.validate as v
    monkeypatch.setattr(v, "fetch_info", fetch_info)

    result = await validate_ticker_node({"ticker": "ZZZZZ"})
    assert result["company_name"] is None
    assert result["validation_error"]  # non-empty friendly message


def test_validate_endpoint_valid(monkeypatch):
    _patch_ticker(monkeypatch, {"AAPL": {"longName": "Apple Inc."}})
    import main
    monkeypatch.setattr(main, "fetch_info", fetch_info)

    with TestClient(app) as client:
        resp = client.post("/validate", json={"ticker": "AAPL"})

    assert resp.status_code == 200
    assert resp.json() == {"valid": True, "company_name": "Apple Inc."}


def test_validate_endpoint_invalid(monkeypatch):
    _patch_ticker(monkeypatch, {})
    import main
    monkeypatch.setattr(main, "fetch_info", fetch_info)

    with TestClient(app) as client:
        resp = client.post("/validate", json={"ticker": "ZZZZZ"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is False
    assert body["error"]


def test_validate_endpoint_empty_string(monkeypatch):
    _patch_ticker(monkeypatch, {})
    import main
    monkeypatch.setattr(main, "fetch_info", fetch_info)

    with TestClient(app) as client:
        resp = client.post("/validate", json={"ticker": ""})

    assert resp.status_code == 200
    assert resp.json()["valid"] is False
