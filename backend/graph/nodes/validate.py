from backend.graph.state import ResearchState


async def validate_ticker_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    return {
        "status_message": f"Looking up {ticker}...",
        "company_name": f"{ticker} Stub Corp.",
        "validation_error": None,
    }
