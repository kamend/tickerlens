from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from clients.anthropic_client import MODEL_SONNET, get_client
from clients.yfinance_client import fetch_news
from graph.state import ResearchState
from prompts import load_prompt

logger = logging.getLogger(__name__)

NEWS_TIMEOUT_SECONDS = 90.0
MAX_TOOL_ITERATIONS = 6


EMIT_NEWS_TOOL: dict[str, Any] = {
    "name": "emit_news",
    "description": "Emit the structured news briefing for the synthesis agent.",
    "input_schema": {
        "type": "object",
        "required": ["direct_news", "macro_context", "implicit_connections"],
        "properties": {
            "direct_news": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["title", "our_note"],
                    "properties": {
                        "title": {"type": "string"},
                        "publisher": {"type": "string"},
                        "date": {"type": "string"},
                        "url": {"type": "string"},
                        "our_note": {"type": "string"},
                    },
                },
            },
            "macro_context": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["topic", "summary"],
                    "properties": {
                        "topic": {"type": "string"},
                        "summary": {"type": "string"},
                        "source_urls": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "implicit_connections": {
                "type": "array",
                "minItems": 0,
                "maxItems": 5,
                "items": {"type": "string"},
            },
        },
    },
}

WEB_SEARCH_TOOL: dict[str, Any] = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 4,
}


def _extract_emit_news(response: Any) -> dict | None:
    for block in getattr(response, "content", []) or []:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == "emit_news":
            return dict(block.input or {})
    return None


async def _analyze_with_sonnet(
    ticker: str,
    company_name: str,
    sector: str | None,
    yfinance_headlines: list[dict],
) -> dict:
    """Run Sonnet with web_search + emit_news, looping until emit_news fires.

    Returns the structured news dict. Raises on failure (caller handles fallback).
    """
    client = get_client()
    system_prompt = load_prompt("news_analyst")

    user_payload = {
        "ticker": ticker,
        "company_name": company_name,
        "sector": sector,
        "yfinance_headlines": yfinance_headlines,
    }
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": json.dumps(user_payload, default=str, indent=2)},
    ]

    for iteration in range(MAX_TOOL_ITERATIONS):
        logger.info("news agent: iteration %d → Anthropic", iteration + 1)
        response = await client.messages.create(
            model=MODEL_SONNET,
            max_tokens=4096,
            system=system_prompt,
            tools=[WEB_SEARCH_TOOL, EMIT_NEWS_TOOL],
            messages=messages,
        )

        block_summary = [
            getattr(b, "type", "?")
            + (f"({getattr(b, 'name', '')})" if getattr(b, "type", None) in ("tool_use", "server_tool_use") else "")
            for b in (response.content or [])
        ]
        logger.info(
            "news agent: stop_reason=%s blocks=%s usage=%s",
            response.stop_reason,
            block_summary,
            getattr(response, "usage", None),
        )

        emitted = _extract_emit_news(response)
        if emitted is not None:
            logger.info("news agent: emit_news received after %d iteration(s)", iteration + 1)
            return emitted

        if response.stop_reason == "end_turn":
            raise RuntimeError("news agent ended turn without calling emit_news")

        # Server tools (web_search) are fulfilled by Anthropic inline within the
        # same response; if we're here without emit_news, Claude called a
        # client-side tool we don't expose, or stopped for another reason.
        # Append assistant turn and nudge it to emit.
        messages.append({"role": "assistant", "content": response.content})
        messages.append(
            {
                "role": "user",
                "content": "Call the emit_news tool now with your findings.",
            }
        )

    raise RuntimeError("news agent exceeded tool-iteration budget")


def _fallback_from_yfinance(yfinance_headlines: list[dict]) -> dict:
    """Build a minimal news payload from yfinance when the LLM path fails."""
    direct_news = [
        {
            "title": item.get("title"),
            "publisher": item.get("publisher"),
            "date": item.get("published_at"),
            "url": item.get("url"),
            "our_note": "Yahoo Finance headline — web_search unavailable, no analyst note.",
        }
        for item in yfinance_headlines
        if item.get("title")
    ]
    return {
        "direct_news": direct_news,
        "macro_context": [],
        "implicit_connections": [],
    }


async def news_agent_node(state: ResearchState) -> dict:
    ticker = state["ticker"]
    company_name = state.get("company_name") or ticker
    status = "Scanning recent news and macro context..."

    yfinance_headlines = await asyncio.to_thread(fetch_news, ticker)
    logger.info(
        "news agent: yfinance returned %d headlines for %s",
        len(yfinance_headlines),
        ticker,
    )

    # Sector may not be available yet if fundamentals hasn't completed — fine,
    # pass None through.
    fundamentals = state.get("fundamentals") or {}
    header = fundamentals.get("header") if isinstance(fundamentals, dict) else None
    sector = header.get("sector") if isinstance(header, dict) else None

    t0 = time.monotonic()
    try:
        news = await asyncio.wait_for(
            _analyze_with_sonnet(ticker, company_name, sector, yfinance_headlines),
            timeout=NEWS_TIMEOUT_SECONDS,
        )
        logger.info("news agent: analysis completed in %.1fs", time.monotonic() - t0)
    except asyncio.TimeoutError:
        logger.warning(
            "news agent timed out for %s after %.1fs, falling back to yfinance-only",
            ticker,
            time.monotonic() - t0,
        )
        news = _fallback_from_yfinance(yfinance_headlines)
    except Exception:
        logger.exception("news agent failed for %s, falling back to yfinance-only", ticker)
        if not yfinance_headlines:
            return {
                "status_message": status,
                "news_error": f"Couldn't gather news for {ticker}.",
            }
        news = _fallback_from_yfinance(yfinance_headlines)

    # Cap implicit connections at 5 per spec (defensive — prompt already asks).
    connections = news.get("implicit_connections") or []
    if len(connections) > 5:
        news["implicit_connections"] = connections[:5]

    return {
        "status_message": status,
        "news": news,
    }
