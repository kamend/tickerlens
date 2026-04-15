from __future__ import annotations

import yfinance


FRIENDLY_NOT_FOUND = "We couldn't find that ticker. Double-check the symbol and try again."


class TickerNotFoundError(Exception):
    """Raised when yfinance has no usable info for a ticker."""

    def __init__(self, ticker: str, message: str = FRIENDLY_NOT_FOUND) -> None:
        super().__init__(message)
        self.ticker = ticker
        self.message = message


def fetch_info(ticker: str) -> dict:
    symbol = (ticker or "").strip().upper()
    if not symbol:
        raise TickerNotFoundError(symbol)

    info = yfinance.Ticker(symbol).get_info() or {}
    if not info.get("longName"):
        raise TickerNotFoundError(symbol)

    return info
