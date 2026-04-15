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
    import graph.nodes.validate as validate_node

    def _fake_fetch_info(ticker: str) -> dict:
        return {"longName": f"{ticker} Stub Corp.", "symbol": ticker}

    monkeypatch.setattr(client, "fetch_info", _fake_fetch_info)
    monkeypatch.setattr(validate_node, "fetch_info", _fake_fetch_info)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "no_mock_yfinance: opt out of the autouse yfinance mock",
    )
