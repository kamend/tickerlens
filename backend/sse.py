import asyncio
import json
import time
from typing import Any, AsyncIterator

MIN_MESSAGE_DISPLAY = 1.2  # seconds


def format_sse(event: str, data: Any) -> str:
    payload = data if isinstance(data, str) else json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


async def pace_events(
    source: AsyncIterator[tuple[str, Any]],
    min_gap: float = MIN_MESSAGE_DISPLAY,
) -> AsyncIterator[tuple[str, Any]]:
    last_emit: float | None = None
    async for event, data in source:
        if last_emit is not None:
            elapsed = time.monotonic() - last_emit
            if elapsed < min_gap:
                await asyncio.sleep(min_gap - elapsed)
        yield event, data
        last_emit = time.monotonic()


async def graph_events(compiled, initial_state: dict) -> AsyncIterator[tuple[str, Any]]:
    """Map LangGraph update stream into (event, data) tuples.

    Consumes stream_mode=["updates","custom"] so nodes can emit early events
    (e.g., the `header` payload from fundamentals) via get_stream_writer()
    before their full state update lands.
    """
    stream = compiled.astream(
        initial_state,
        stream_mode=["updates", "custom"],
    )
    async for mode, chunk in stream:
        if mode == "custom":
            if isinstance(chunk, dict) and isinstance(chunk.get("header"), dict):
                yield "header", chunk["header"]
            continue

        # mode == "updates"
        for node, delta in chunk.items():
            if not isinstance(delta, dict):
                continue

            if delta.get("validation_error"):
                yield "error", {"message": delta["validation_error"]}
                return

            status = delta.get("status_message")
            if status:
                yield "progress", {"node": node, "message": status}

            briefing = delta.get("briefing")
            if briefing is not None:
                yield "result", briefing

            error = delta.get("error")
            if error:
                yield "error", {"message": error}
                return
