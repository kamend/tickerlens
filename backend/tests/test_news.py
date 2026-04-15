import asyncio
from types import SimpleNamespace

import pytest

import graph.nodes.news as news_node


pytestmark = pytest.mark.no_mock_yfinance


@pytest.fixture
def yfinance_headlines():
    return [
        {
            "title": "Apple announces record services revenue",
            "publisher": "Reuters",
            "published_at": "2026-04-10",
            "url": "https://example.com/apple-services",
        },
        {
            "title": "EU opens new DMA probe into App Store",
            "publisher": "FT",
            "published_at": "2026-04-12",
            "url": "https://example.com/dma-probe",
        },
    ]


@pytest.fixture(autouse=True)
def _patch_yfinance(monkeypatch, yfinance_headlines):
    monkeypatch.setattr(news_node, "fetch_news", lambda _t, limit=8: list(yfinance_headlines))


async def test_happy_path_returns_three_sections(monkeypatch):
    expected = {
        "direct_news": [
            {
                "title": "Apple announces record services revenue",
                "publisher": "Reuters",
                "date": "2026-04-10",
                "url": "https://example.com/apple-services",
                "our_note": "Services mix continues to expand.",
            }
        ],
        "macro_context": [
            {
                "topic": "EU Digital Markets Act enforcement",
                "summary": "New probes signal tighter App Store rules.",
                "source_urls": ["https://example.com/dma-probe"],
            }
        ],
        "implicit_connections": [
            "DMA enforcement → services-revenue compression risk",
            "China reopening → iPhone demand tailwind",
            "USD strength → FX drag on international segments",
        ],
    }

    async def _fake_analyze(*_a, **_kw):
        return expected

    monkeypatch.setattr(news_node, "_analyze_with_sonnet", _fake_analyze)

    out = await news_node.news_agent_node({"ticker": "AAPL", "company_name": "Apple Inc."})

    assert out["status_message"] == "Scanning recent news and macro context..."
    assert out["news"]["direct_news"] == expected["direct_news"]
    assert out["news"]["macro_context"] == expected["macro_context"]
    assert len(out["news"]["implicit_connections"]) == 3


async def test_implicit_connections_capped_at_five(monkeypatch):
    async def _fake_analyze(*_a, **_kw):
        return {
            "direct_news": [],
            "macro_context": [],
            "implicit_connections": [f"connection {i}" for i in range(10)],
        }

    monkeypatch.setattr(news_node, "_analyze_with_sonnet", _fake_analyze)

    out = await news_node.news_agent_node({"ticker": "AAPL"})
    assert len(out["news"]["implicit_connections"]) == 5


async def test_timeout_falls_back_to_yfinance(monkeypatch, yfinance_headlines):
    async def _hang(*_a, **_kw):
        await asyncio.sleep(10)
        return {}

    monkeypatch.setattr(news_node, "_analyze_with_sonnet", _hang)
    monkeypatch.setattr(news_node, "NEWS_TIMEOUT_SECONDS", 0.05)

    out = await news_node.news_agent_node({"ticker": "AAPL"})

    assert "news_error" not in out
    assert len(out["news"]["direct_news"]) == len(yfinance_headlines)
    assert out["news"]["implicit_connections"] == []


async def test_anthropic_failure_falls_back_when_yfinance_has_items(monkeypatch):
    async def _boom(*_a, **_kw):
        raise RuntimeError("web_search 500")

    monkeypatch.setattr(news_node, "_analyze_with_sonnet", _boom)

    out = await news_node.news_agent_node({"ticker": "AAPL"})

    assert "news_error" not in out
    assert len(out["news"]["direct_news"]) == 2


async def test_anthropic_failure_and_no_yfinance_sets_error(monkeypatch):
    async def _boom(*_a, **_kw):
        raise RuntimeError("web_search 500")

    monkeypatch.setattr(news_node, "fetch_news", lambda _t, limit=8: [])
    monkeypatch.setattr(news_node, "_analyze_with_sonnet", _boom)

    out = await news_node.news_agent_node({"ticker": "AAPL"})

    assert "news_error" in out
    assert "news" not in out


async def test_extract_emit_news_finds_tool_call():
    block_text = SimpleNamespace(type="text", text="Searching...")
    block_tool = SimpleNamespace(
        type="tool_use",
        name="emit_news",
        input={"direct_news": [], "macro_context": [], "implicit_connections": []},
    )
    response = SimpleNamespace(content=[block_text, block_tool])

    result = news_node._extract_emit_news(response)
    assert result == {"direct_news": [], "macro_context": [], "implicit_connections": []}


async def test_extract_emit_news_returns_none_when_missing():
    response = SimpleNamespace(content=[SimpleNamespace(type="text", text="hi")])
    assert news_node._extract_emit_news(response) is None


async def test_analyze_loops_until_emit(monkeypatch):
    """If the first response doesn't include emit_news, the loop nudges and retries."""
    calls = {"n": 0}

    class FakeClient:
        def __init__(self):
            self.messages = self

        async def create(self, **_kw):
            calls["n"] += 1
            if calls["n"] == 1:
                # Simulate a response with only a text block and non-end_turn stop.
                return SimpleNamespace(
                    content=[SimpleNamespace(type="text", text="thinking")],
                    stop_reason="tool_use",
                )
            return SimpleNamespace(
                content=[
                    SimpleNamespace(
                        type="tool_use",
                        name="emit_news",
                        input={
                            "direct_news": [],
                            "macro_context": [],
                            "implicit_connections": ["late connection"],
                        },
                    )
                ],
                stop_reason="tool_use",
            )

    monkeypatch.setattr(news_node, "get_client", lambda: FakeClient())
    monkeypatch.setattr(news_node, "load_prompt", lambda _n: "system")

    result = await news_node._analyze_with_sonnet("AAPL", "Apple Inc.", "Technology", [])

    assert result["implicit_connections"] == ["late connection"]
    assert calls["n"] == 2
