import pytest

from graph.graph import build_graph


@pytest.fixture
def compiled():
    return build_graph()


async def _collect_updates(compiled, state):
    updates = []
    async for update in compiled.astream(state, stream_mode="updates"):
        updates.append(update)
    return updates


async def test_graph_emits_expected_node_sequence(compiled):
    updates = await _collect_updates(compiled, {"ticker": "FAKE"})
    nodes_in_order = [list(u.keys())[0] for u in updates]

    assert nodes_in_order[0] == "validate"
    assert nodes_in_order[-1] == "synthesis"
    assert "fundamentals" in nodes_in_order
    assert "news" in nodes_in_order

    fundamentals_idx = nodes_in_order.index("fundamentals")
    news_idx = nodes_in_order.index("news")
    synthesis_idx = nodes_in_order.index("synthesis")
    validate_idx = nodes_in_order.index("validate")

    assert validate_idx < fundamentals_idx < synthesis_idx
    assert validate_idx < news_idx < synthesis_idx


async def test_fan_out_both_branches_fire_before_synthesis(compiled):
    updates = await _collect_updates(compiled, {"ticker": "FAKE"})
    nodes_in_order = [list(u.keys())[0] for u in updates]

    pre_synthesis = nodes_in_order[: nodes_in_order.index("synthesis")]
    assert "fundamentals" in pre_synthesis
    assert "news" in pre_synthesis


async def test_status_messages_populated_per_node(compiled):
    updates = await _collect_updates(compiled, {"ticker": "FAKE"})

    by_node = {list(u.keys())[0]: list(u.values())[0] for u in updates}
    assert "Looking up" in by_node["validate"]["status_message"]
    assert "fundamentals" in by_node["fundamentals"]["status_message"]
    assert "news" in by_node["news"]["status_message"].lower()
    assert by_node["synthesis"]["briefing"] is not None
