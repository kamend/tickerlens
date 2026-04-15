import pytest


@pytest.fixture(autouse=True)
def _mock_yfinance_for_graph(request, monkeypatch):
    """Keep graph/SSE tests off the network.

    Tests that exercise the yfinance client directly opt out via the
    `no_mock_yfinance` marker.
    """
    if request.node.get_closest_marker("no_mock_yfinance"):
        return

    import clients.yfinance_client as client
    import graph.nodes.fundamentals as fundamentals_node
    import graph.nodes.validate as validate_node

    def _fake_fetch_info(ticker: str) -> dict:
        return {
            "longName": f"{ticker} Stub Corp.",
            "symbol": ticker,
            "sector": "Technology",
            "currentPrice": 100.0,
            "previousClose": 98.0,
            "marketCap": 1_000_000_000,
            "trailingPE": 20.0,
            "fiftyTwoWeekLow": 80.0,
            "fiftyTwoWeekHigh": 120.0,
            "dividendYield": 0.01,
            "longBusinessSummary": "A stubbed company for tests.",
        }

    async def _fake_summary(_raw_metrics: dict) -> str:
        return "Stubbed Sonnet summary."

    monkeypatch.setattr(client, "fetch_info", _fake_fetch_info)
    monkeypatch.setattr(validate_node, "fetch_info", _fake_fetch_info)
    monkeypatch.setattr(fundamentals_node, "fetch_info", _fake_fetch_info)
    monkeypatch.setattr(fundamentals_node, "_summarize_with_sonnet", _fake_summary)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "no_mock_yfinance: opt out of the autouse yfinance mock",
    )
