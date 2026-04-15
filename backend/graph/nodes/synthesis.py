from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from clients.anthropic_client import MODEL_OPUS, get_client
from graph.state import ResearchState
from prompts import load_prompt
from schemas.briefing import Briefing

logger = logging.getLogger(__name__)


ARGUMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["summary", "reasoning", "confidence", "citations"],
    "properties": {
        "summary": {
            "type": "string",
            "description": "2-3 sentence collapsed-card summary.",
        },
        "reasoning": {
            "type": "string",
            "description": "3-5 paragraphs of full reasoning prose.",
        },
        "confidence": {
            "type": "string",
            "enum": ["strong", "moderate", "thin"],
        },
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title", "url"],
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                },
            },
        },
    },
}

EMIT_BRIEFING_TOOL: dict[str, Any] = {
    "name": "emit_briefing",
    "description": "Emit the final Buy/Hold/Sell briefing for the investor.",
    "input_schema": {
        "type": "object",
        "required": ["buy", "hold", "sell"],
        "properties": {
            "buy": ARGUMENT_SCHEMA,
            "hold": ARGUMENT_SCHEMA,
            "sell": ARGUMENT_SCHEMA,
        },
    },
}


def _extract_emit_briefing(response: Any) -> dict | None:
    for block in getattr(response, "content", []) or []:
        if (
            getattr(block, "type", None) == "tool_use"
            and getattr(block, "name", None) == "emit_briefing"
        ):
            return dict(block.input or {})
    return None


async def _synthesize_with_opus(
    ticker: str,
    company_name: str,
    fundamentals: dict,
    news: dict,
) -> Briefing:
    client = get_client()
    system_prompt = load_prompt("synthesis")

    user_payload = {
        "ticker": ticker,
        "company_name": company_name,
        "fundamentals": {
            "summary": fundamentals.get("summary"),
            "raw_metrics": fundamentals.get("raw_metrics"),
        },
        "news": {
            "direct_news": news.get("direct_news", []),
            "macro_context": news.get("macro_context", []),
            "implicit_connections": news.get("implicit_connections", []),
        },
    }

    response = await client.messages.create(
        model=MODEL_OPUS,
        max_tokens=4096,
        system=system_prompt,
        tools=[EMIT_BRIEFING_TOOL],
        tool_choice={"type": "tool", "name": "emit_briefing"},
        messages=[
            {"role": "user", "content": json.dumps(user_payload, default=str, indent=2)},
        ],
    )

    logger.info(
        "synthesis agent: stop_reason=%s usage=%s",
        response.stop_reason,
        getattr(response, "usage", None),
    )

    emitted = _extract_emit_briefing(response)
    if emitted is None:
        raise RuntimeError("synthesis agent did not call emit_briefing")

    return Briefing.model_validate(emitted)


async def synthesis_agent_node(state: ResearchState) -> dict:
    if state.get("fundamentals_error"):
        return {
            "status_message": "Unable to complete research.",
            "error": state["fundamentals_error"],
        }
    if state.get("news_error"):
        return {
            "status_message": "Unable to complete research.",
            "error": state["news_error"],
        }

    ticker = state["ticker"]
    company_name = state.get("company_name") or ticker
    fundamentals = state.get("fundamentals") or {}
    news = state.get("news") or {}
    status = "Building the case for each perspective..."

    try:
        briefing = await _synthesize_with_opus(ticker, company_name, fundamentals, news)
    except ValidationError as exc:
        logger.exception("synthesis agent: emit_briefing output failed validation")
        return {
            "status_message": status,
            "error": f"Synthesis output was malformed: {exc.errors()[0]['msg']}",
        }
    except Exception as exc:
        logger.exception("synthesis agent failed for %s", ticker)
        return {
            "status_message": status,
            "error": f"Couldn't build the briefing for {ticker}.",
        }

    return {
        "status_message": status,
        "briefing": briefing.model_dump(),
    }
