from langgraph.graph import END, START, StateGraph

from backend.graph.nodes.fundamentals import fundamentals_agent_node
from backend.graph.nodes.news import news_agent_node
from backend.graph.nodes.synthesis import synthesis_agent_node
from backend.graph.nodes.validate import validate_ticker_node
from backend.graph.state import ResearchState


def _route_after_validate(state: ResearchState):
    if state.get("validation_error"):
        return END
    # Returning a list triggers LangGraph's fan-out: both nodes run in parallel
    # within the same super-step.
    return ["fundamentals", "news"]


def build_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("validate", validate_ticker_node)
    graph.add_node("fundamentals", fundamentals_agent_node)
    graph.add_node("news", news_agent_node)
    graph.add_node("synthesis", synthesis_agent_node)

    graph.add_edge(START, "validate")
    graph.add_conditional_edges("validate", _route_after_validate)
    graph.add_edge("fundamentals", "synthesis")
    graph.add_edge("news", "synthesis")
    graph.add_edge("synthesis", END)

    return graph.compile()


compiled = build_graph()
