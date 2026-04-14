import time

import pytest

from sse import MIN_MESSAGE_DISPLAY, format_sse, pace_events


def test_format_sse_wire_format():
    out = format_sse("progress", {"node": "validate", "message": "Looking up AAPL..."})
    assert out.startswith("event: progress\n")
    assert "data: " in out
    assert out.endswith("\n\n")
    # Two newlines separate events on the wire
    assert out.count("\n\n") == 1


def test_format_sse_string_passthrough():
    out = format_sse("progress", "hello")
    assert out == "event: progress\ndata: hello\n\n"


async def _async_iter(items):
    for item in items:
        yield item


async def test_pace_events_enforces_minimum_gap():
    events = [("progress", {"n": 1}), ("progress", {"n": 2})]

    start = time.monotonic()
    collected = []
    async for ev in pace_events(_async_iter(events), min_gap=0.3):
        collected.append((time.monotonic() - start, ev))

    assert len(collected) == 2
    gap = collected[1][0] - collected[0][0]
    assert gap >= 0.3 - 0.05, f"gap {gap} below min_gap"


async def test_pace_events_respects_default_min_gap():
    # Use a tiny subset to keep test fast but confirm the default constant wires through.
    events = [("progress", {"n": 1}), ("progress", {"n": 2})]

    timestamps = []
    async for _event, _data in pace_events(_async_iter(events)):
        timestamps.append(time.monotonic())

    gap = timestamps[1] - timestamps[0]
    assert gap >= MIN_MESSAGE_DISPLAY - 0.05


async def test_pace_events_first_emits_immediately():
    events = [("progress", {"n": 1})]
    start = time.monotonic()
    async for _ in pace_events(_async_iter(events), min_gap=1.0):
        first_at = time.monotonic() - start
    assert first_at < 0.2
