"""Quick diagnostic for yfinance behavior.

Run from backend/:
    uv run python scripts/debug_yfinance.py AAPL
    uv run python scripts/debug_yfinance.py ZZZZZ

Exercises several lookup paths so we can see which ones actually work on
this machine / yfinance version, and what the raw failure mode looks like.
"""
from __future__ import annotations

import sys
import traceback

import yfinance


def banner(label: str) -> None:
    print("\n" + "=" * 60)
    print(label)
    print("=" * 60)


def try_call(label: str, fn):
    banner(label)
    try:
        result = fn()
    except Exception as exc:
        print(f"EXCEPTION: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return None
    print(f"type: {type(result).__name__}")
    if isinstance(result, dict):
        print(f"keys ({len(result)}): {sorted(result)[:25]}{'...' if len(result) > 25 else ''}")
        for k in ("longName", "shortName", "symbol", "quoteType", "regularMarketPrice"):
            if k in result:
                print(f"  {k} = {result[k]!r}")
    else:
        print(repr(result)[:400])
    return result


def main(symbol: str) -> None:
    print(f"yfinance version: {yfinance.__version__}")
    print(f"probe symbol:     {symbol!r}")

    t = yfinance.Ticker(symbol)
    try_call("Ticker.info", lambda: t.info)
    try_call("Ticker.fast_info", lambda: dict(t.fast_info))
    try_call("Ticker.get_info()", lambda: t.get_info())
    try_call("Ticker.history(period='1d')", lambda: t.history(period="1d").to_dict())
    try_call("yfinance.Tickers().tickers", lambda: list(yfinance.Tickers(symbol).tickers.keys()))


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    main(ticker)
