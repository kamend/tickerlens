"""One-shot debug for the validate step.

Times three layers independently so you can see exactly where latency lives:
  1. raw yfinance.Ticker(...).get_info()
  2. clients.yfinance_client.fetch_info  (same call + our error normalization)
  3. graph.nodes.validate.validate_ticker_node  (what the graph actually runs)

Usage:
    uv run python scripts/run_validate.py AAPL
    uv run python scripts/run_validate.py FIG --runs 3
    uv run python scripts/run_validate.py ZZZZZ
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yfinance  # noqa: E402

from clients.yfinance_client import (  # noqa: E402
    TickerNotFoundError,
    fetch_info,
)
from graph.nodes.validate import validate_ticker_node  # noqa: E402


def _time(label: str, fn):
    start = time.perf_counter()
    try:
        result = fn()
        elapsed = time.perf_counter() - start
        print(f"  {label:<38} {elapsed*1000:>8.1f} ms   OK")
        return result, elapsed, None
    except Exception as exc:
        elapsed = time.perf_counter() - start
        print(f"  {label:<38} {elapsed*1000:>8.1f} ms   {type(exc).__name__}: {exc}")
        return None, elapsed, exc


async def run_once(ticker: str, run_index: int) -> None:
    print(f"\n=== run {run_index}  ticker={ticker} ===")

    print("[1] raw yfinance.Ticker().get_info()")
    info, _, _ = _time(
        "yfinance.Ticker(symbol).get_info()",
        lambda: yfinance.Ticker(ticker).get_info() or {},
    )
    if info:
        print(f"      longName={info.get('longName')!r}  "
              f"keys={len(info)}")

    print("[2] clients.yfinance_client.fetch_info")
    try:
        start = time.perf_counter()
        info2 = fetch_info(ticker)
        elapsed = time.perf_counter() - start
        print(f"  {'fetch_info':<38} {elapsed*1000:>8.1f} ms   OK  "
              f"longName={info2.get('longName')!r}")
    except TickerNotFoundError as exc:
        elapsed = time.perf_counter() - start
        print(f"  {'fetch_info':<38} {elapsed*1000:>8.1f} ms   "
              f"TickerNotFoundError: {exc.message}")

    print("[3] validate_ticker_node (graph node)")
    start = time.perf_counter()
    out = await validate_ticker_node({"ticker": ticker})
    elapsed = time.perf_counter() - start
    print(f"  {'validate_ticker_node':<38} {elapsed*1000:>8.1f} ms   OK")
    print(f"      company_name={out.get('company_name')!r}")
    print(f"      validation_error={out.get('validation_error')!r}")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", nargs="?", default="AAPL")
    parser.add_argument("--runs", type=int, default=1,
                        help="Run the full sequence N times (to spot cold-cache effects)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    overall = time.perf_counter()
    for i in range(1, args.runs + 1):
        await run_once(args.ticker, i)
    print(f"\ntotal wall time: {(time.perf_counter()-overall)*1000:.1f} ms")


if __name__ == "__main__":
    asyncio.run(main())
