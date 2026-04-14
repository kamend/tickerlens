from backend.graph.state import ResearchState


async def news_agent_node(state: ResearchState) -> dict:
    return {
        "status_message": "Scanning recent news and macro context...",
        "news": {
            "direct_news": [],
            "macro_context": [],
            "implicit_connections": ["Stub implicit connection."],
        },
    }
