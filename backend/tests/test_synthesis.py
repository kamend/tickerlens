from types import SimpleNamespace

import pytest

import graph.nodes.synthesis as synthesis_node
from schemas.briefing import Argument, Briefing, Citation

pytestmark = pytest.mark.no_mock_yfinance


def _good_arg(label: str) -> dict:
    return {
        "summary": f"{label} summary.",
        "reasoning": f"{label} reasoning paragraph.",
        "confidence": "moderate",
        "citations": [{"title": "Src", "url": "https://example.com"}],
    }


def _good_tool_input() -> dict:
    return {"buy": _good_arg("buy"), "hold": _good_arg("hold"), "sell": _good_arg("sell")}


@pytest.fixture
def base_state():
    return {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "fundamentals": {
            "summary": "Balanced posture.",
            "raw_metrics": {"trailingPE": 30.0},
        },
        "news": {
            "direct_news": [],
            "macro_context": [],
            "implicit_connections": ["DMA → services risk"],
        },
    }


async def test_happy_path_populates_briefing(monkeypatch, base_state):
    async def _fake(*_a, **_kw):
        return Briefing(
            buy=Argument(**_good_arg("buy")),
            hold=Argument(**_good_arg("hold")),
            sell=Argument(**_good_arg("sell")),
        )

    monkeypatch.setattr(synthesis_node, "_synthesize_with_opus", _fake)
    out = await synthesis_node.synthesis_agent_node(base_state)

    assert out["status_message"] == "Building the case for each perspective..."
    assert "error" not in out
    assert set(out["briefing"].keys()) == {"buy", "hold", "sell"}
    assert out["briefing"]["buy"]["confidence"] == "moderate"
    assert out["briefing"]["buy"]["citations"][0]["url"] == "https://example.com"


async def test_fundamentals_error_short_circuits(base_state):
    state = {**base_state, "fundamentals_error": "yfinance blew up"}
    out = await synthesis_node.synthesis_agent_node(state)
    assert out["error"] == "yfinance blew up"
    assert "briefing" not in out


async def test_news_error_short_circuits(base_state):
    state = {**base_state, "news_error": "news pipeline down"}
    out = await synthesis_node.synthesis_agent_node(state)
    assert out["error"] == "news pipeline down"
    assert "briefing" not in out


async def test_opus_failure_sets_state_error(monkeypatch, base_state):
    async def _boom(*_a, **_kw):
        raise RuntimeError("Opus 500")

    monkeypatch.setattr(synthesis_node, "_synthesize_with_opus", _boom)
    out = await synthesis_node.synthesis_agent_node(base_state)

    assert "briefing" not in out
    assert "error" in out
    assert "AAPL" in out["error"]


async def test_extract_emit_briefing_finds_tool_call():
    block = SimpleNamespace(type="tool_use", name="emit_briefing", input=_good_tool_input())
    response = SimpleNamespace(content=[block])
    assert synthesis_node._extract_emit_briefing(response) == _good_tool_input()


async def test_extract_emit_briefing_returns_none_when_missing():
    response = SimpleNamespace(content=[SimpleNamespace(type="text", text="hi")])
    assert synthesis_node._extract_emit_briefing(response) is None


async def test_synthesize_with_opus_parses_tool_call(monkeypatch):
    class FakeClient:
        def __init__(self):
            self.messages = self

        async def create(self, **_kw):
            return SimpleNamespace(
                content=[
                    SimpleNamespace(
                        type="tool_use",
                        name="emit_briefing",
                        input=_good_tool_input(),
                    )
                ],
                stop_reason="tool_use",
                usage=None,
            )

    monkeypatch.setattr(synthesis_node, "get_client", lambda: FakeClient())
    monkeypatch.setattr(synthesis_node, "load_prompt", lambda _n: "system")

    briefing = await synthesis_node._synthesize_with_opus(
        "AAPL", "Apple Inc.", {"summary": "s", "raw_metrics": {}}, {}
    )
    assert isinstance(briefing, Briefing)
    assert briefing.hold.summary == "hold summary."


async def test_synthesize_with_opus_raises_when_tool_missing(monkeypatch):
    class FakeClient:
        def __init__(self):
            self.messages = self

        async def create(self, **_kw):
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text="I refuse")],
                stop_reason="end_turn",
                usage=None,
            )

    monkeypatch.setattr(synthesis_node, "get_client", lambda: FakeClient())
    monkeypatch.setattr(synthesis_node, "load_prompt", lambda _n: "system")

    with pytest.raises(RuntimeError, match="emit_briefing"):
        await synthesis_node._synthesize_with_opus("AAPL", "Apple Inc.", {}, {})


async def test_invalid_confidence_enum_becomes_state_error(monkeypatch, base_state):
    bad = {
        "buy": {**_good_arg("buy"), "confidence": "definitely-yes"},
        "hold": _good_arg("hold"),
        "sell": _good_arg("sell"),
    }

    class FakeClient:
        def __init__(self):
            self.messages = self

        async def create(self, **_kw):
            return SimpleNamespace(
                content=[SimpleNamespace(type="tool_use", name="emit_briefing", input=bad)],
                stop_reason="tool_use",
                usage=None,
            )

    monkeypatch.setattr(synthesis_node, "get_client", lambda: FakeClient())
    monkeypatch.setattr(synthesis_node, "load_prompt", lambda _n: "system")

    out = await synthesis_node.synthesis_agent_node(base_state)
    assert "briefing" not in out
    assert "error" in out
