"""One-shot verification for the news agent (step 6).

Runs the real yfinance fetch + real Sonnet/web_search call end to end and
pretty-prints the structured output.

Usage:
    uv run python scripts/run_news.py AAPL
    uv run python scripts/run_news.py AAPL --timeout 90
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import graph.nodes.news as news_node  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", nargs="?", default="AAPL")
    parser.add_argument("--timeout", type=float, default=90.0,
                        help="Override NEWS_TIMEOUT_SECONDS for this run")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    news_node.NEWS_TIMEOUT_SECONDS = args.timeout

    out = await news_node.news_agent_node(
        {"ticker": args.ticker, "company_name": args.ticker}
    )
    if "news_error" in out:
        print(f"NEWS ERROR: {out['news_error']}")
        return
    print("\n--- NEWS PAYLOAD ---")
    print(json.dumps(out["news"], indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
