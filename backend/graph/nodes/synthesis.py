from graph.state import ResearchState


async def synthesis_agent_node(state: ResearchState) -> dict:
    if state.get("fundamentals_error") or state.get("news_error"):
        return {
            "status_message": "Unable to complete research.",
            "error": "Upstream agent failure.",
        }

    return {
        "status_message": "Building the case for each perspective...",
        "briefing": {
            "buy": {"summary": "stub", "reasoning": "stub", "confidence": "thin", "citations": []},
            "hold": {"summary": "stub", "reasoning": "stub", "confidence": "thin", "citations": []},
            "sell": {"summary": "stub", "reasoning": "stub", "confidence": "thin", "citations": []},
        },
    }
