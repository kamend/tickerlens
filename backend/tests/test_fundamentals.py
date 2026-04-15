import pytest

import graph.nodes.fundamentals as fundamentals_node
from clients.yfinance_client import TickerNotFoundError
from sse import graph_events


pytestmark = pytest.mark.no_mock_yfinance


@pytest.fixture
def fake_info():
    return {
        "longName": "Apple Inc.",
        "symbol": "AAPL",
        "sector": "Technology",
        "currentPrice": 200.0,
        "previousClose": 195.0,
        "marketCap": 3_000_000_000_000,
        "trailingPE": 32.5,
        "fiftyTwoWeekLow": 150.0,
        "fiftyTwoWeekHigh": 220.0,
        "dividendYield": 0.005,
        "forwardPE": 28.0,
        "priceToBook": 50.0,
        "profitMargins": 0.25,
        "returnOnEquity": 1.4,
        "debtToEquity": 150.0,
        "revenueGrowth": 0.05,
        "earningsGrowth": 0.08,
        "longBusinessSummary": "Apple designs, manufactures, and markets...",
    }


@pytest.fixture(autouse=True)
def _patch_external(monkeypatch, fake_info):
    monkeypatch.setattr(fundamentals_node, "fetch_info", lambda _t: fake_info)

    async def _fake_summary(_raw_metrics):
        return "Apple sits as a mature cash machine. Trailing P/E of 32.5 is rich."

    monkeypatch.setattr(fundamentals_node, "_summarize_with_sonnet", _fake_summary)

    # The graph-level test below runs the full compiled graph, which includes
    # the news node. Stub its external I/O here too.
    import graph.nodes.news as news_node

    async def _fake_news_analyze(*_a, **_kw):
        return {
            "direct_news": [],
            "macro_context": [],
            "implicit_connections": ["Stubbed connection."],
        }

    monkeypatch.setattr(news_node, "fetch_news", lambda _t, limit=8: [])
    monkeypatch.setattr(news_node, "_analyze_with_sonnet", _fake_news_analyze)


async def test_header_contains_six_required_fields():
    out = await fundamentals_node.fundamentals_agent_node(
        {"ticker": "AAPL", "company_name": "Apple Inc."}
    )

    header = out["fundamentals"]["header"]
    assert header["company_name"] == "Apple Inc."
    assert header["ticker"] == "AAPL"
    assert header["sector"] == "Technology"
    assert header["price"] == 200.0
    metrics = header["metrics"]
    assert metrics["market_cap"] == 3_000_000_000_000
    assert metrics["pe_trailing"] == 32.5
    assert metrics["fifty_two_week_low"] == 150.0
    assert metrics["fifty_two_week_high"] == 220.0
    assert metrics["dividend_yield"] == 0.005
    # %change = (200 - 195) / 195 * 100
    assert metrics["change_pct"] == pytest.approx(2.56, abs=0.01)


async def test_raw_metrics_includes_extra_fields():
    out = await fundamentals_node.fundamentals_agent_node({"ticker": "AAPL"})
    raw = out["fundamentals"]["raw_metrics"]

    for key in ("forwardPE", "priceToBook", "profitMargins", "returnOnEquity",
                "debtToEquity", "revenueGrowth", "earningsGrowth", "longBusinessSummary"):
        assert key in raw


async def test_status_message_emitted_first():
    out = await fundamentals_node.fundamentals_agent_node(
        {"ticker": "AAPL", "company_name": "Apple Inc."}
    )
    assert out["status_message"] == "Reading Apple Inc.'s fundamentals..."


async def test_summary_populated():
    out = await fundamentals_node.fundamentals_agent_node({"ticker": "AAPL"})
    assert "Apple" in out["fundamentals"]["summary"]


async def test_ticker_not_found_sets_error(monkeypatch):
    def _raise(_t):
        raise TickerNotFoundError("ZZZZ")

    monkeypatch.setattr(fundamentals_node, "fetch_info", _raise)

    out = await fundamentals_node.fundamentals_agent_node({"ticker": "ZZZZ"})
    assert "fundamentals_error" in out
    assert "fundamentals" not in out


async def test_anthropic_failure_sets_error(monkeypatch):
    async def _fail(_raw):
        raise RuntimeError("anthropic exploded")

    monkeypatch.setattr(fundamentals_node, "_summarize_with_sonnet", _fail)

    out = await fundamentals_node.fundamentals_agent_node({"ticker": "AAPL"})
    assert "fundamentals_error" in out
    assert "anthropic exploded" in out["fundamentals_error"]


async def test_dividend_yield_optional(monkeypatch, fake_info):
    info = {**fake_info, "dividendYield": None}
    monkeypatch.setattr(fundamentals_node, "fetch_info", lambda _t: info)

    out = await fundamentals_node.fundamentals_agent_node({"ticker": "AAPL"})
    assert out["fundamentals"]["header"]["metrics"]["dividend_yield"] is None


async def test_sse_emits_header_event_before_summary_completes(monkeypatch):
    """Strategy C: the `header` SSE event must arrive while the Sonnet
    summary call is still running, not after it returns."""
    import asyncio

    import graph.nodes.fundamentals as fn
    from graph.graph import build_graph
    from sse import graph_events

    summary_started = asyncio.Event()
    release_summary = asyncio.Event()

    async def _slow_summary(_raw):
        summary_started.set()
        await release_summary.wait()
        return "Slow summary that blocks until header is observed."

    monkeypatch.setattr(fn, "_summarize_with_sonnet", _slow_summary)

    compiled = build_graph()
    events = []

    async def _consume():
        async for event, data in graph_events(compiled, {"ticker": "AAPL"}):
            events.append((event, data))
            if event == "header":
                # Prove we got the header while summary is still blocked
                assert summary_started.is_set()
                assert not release_summary.is_set()
                release_summary.set()

    await asyncio.wait_for(_consume(), timeout=5.0)

    event_types = [e for e, _ in events]
    assert "header" in event_types
    assert "result" in event_types
    assert event_types.index("header") < event_types.index("result")
