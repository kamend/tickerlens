import asyncio

from clients.yfinance_client import TickerNotFoundError, fetch_info
from graph.state import ResearchState


async def validate_ticker_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    try:
        info = await asyncio.to_thread(fetch_info, ticker)
    except TickerNotFoundError as exc:
        return {
            "status_message": f"Looking up {ticker}...",
            "company_name": None,
            "validation_error": exc.message,
        }

    return {
        "status_message": f"Looking up {ticker}...",
        "company_name": info["longName"],
        "validation_error": None,
    }
