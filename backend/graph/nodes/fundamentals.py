from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from langgraph.config import get_stream_writer

from clients.anthropic_client import MODEL_SONNET, get_client
from clients.yfinance_client import TickerNotFoundError, fetch_info
from graph.state import ResearchState
from prompts import load_prompt

logger = logging.getLogger(__name__)


HEADER_FIELDS = (
    "longName",
    "symbol",
    "sector",
    "currentPrice",
    "previousClose",
    "marketCap",
    "trailingPE",
    "fiftyTwoWeekLow",
    "fiftyTwoWeekHigh",
    "dividendYield",
)

RAW_EXTRA_FIELDS = (
    "forwardPE",
    "priceToBook",
    "profitMargins",
    "returnOnEquity",
    "debtToEquity",
    "revenueGrowth",
    "earningsGrowth",
    "longBusinessSummary",
)


def _pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return round((current - previous) / previous * 100, 2)


def _build_header(info: dict, ticker: str) -> dict[str, Any]:
    price = info.get("currentPrice")
    return {
        "company_name": info.get("longName") or ticker,
        "ticker": info.get("symbol") or ticker,
        "sector": info.get("sector"),
        "price": price,
        "metrics": {
            "market_cap": info.get("marketCap"),
            "pe_trailing": info.get("trailingPE"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "dividend_yield": info.get("dividendYield"),
            "change_pct": _pct_change(price, info.get("previousClose")),
        },
    }


def _build_raw_metrics(info: dict) -> dict[str, Any]:
    keys = HEADER_FIELDS + RAW_EXTRA_FIELDS
    return {k: info.get(k) for k in keys}


async def _summarize_with_sonnet(raw_metrics: dict) -> str:
    client = get_client()
    system_prompt = load_prompt("fundamentals_summary")
    response = await client.messages.create(
        model=MODEL_SONNET,
        max_tokens=600,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": json.dumps(raw_metrics, default=str, indent=2),
            }
        ],
    )
    parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "\n\n".join(parts).strip()


async def fundamentals_agent_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    company_name = state.get("company_name") or ticker
    status = f"Reading {company_name}'s fundamentals..."

    try:
        info = await asyncio.to_thread(fetch_info, ticker)
        header = _build_header(info, ticker)
        raw_metrics = _build_raw_metrics(info)

        # Emit the header to the custom stream channel BEFORE the slow Sonnet
        # call. The SSE adapter consumes stream_mode=["updates","custom"] and
        # forwards this as a `header` SSE event, so the UI can render the
        # company card while the summary is still being written.
        try:
            writer = get_stream_writer()
            writer({"header": header})
        except RuntimeError:
            # Outside a graph run (e.g., unit-testing the node directly).
            pass

        summary = await _summarize_with_sonnet(raw_metrics)
    except TickerNotFoundError as exc:
        return {
            "status_message": status,
            "fundamentals_error": exc.message,
        }
    except Exception as exc:
        logger.exception("fundamentals agent failed for %s", ticker)
        return {
            "status_message": status,
            "fundamentals_error": f"Couldn't read fundamentals for {ticker}: {exc}",
        }

    return {
        "status_message": status,
        "fundamentals": {
            "header": header,
            "raw_metrics": raw_metrics,
            "summary": summary,
        },
    }
