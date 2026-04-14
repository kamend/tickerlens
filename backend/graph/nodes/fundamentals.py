from graph.state import ResearchState


async def fundamentals_agent_node(state: ResearchState) -> dict:
    company_name = state.get("company_name") or state["ticker"]
    return {
        "status_message": f"Reading {company_name}'s fundamentals...",
        "fundamentals": {
            "header": {"stub": True, "ticker": state["ticker"]},
            "raw_metrics": {"stub": True},
            "summary": "Stub fundamentals summary.",
        },
    }
