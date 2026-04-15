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


def fetch_news(ticker: str, limit: int = 8) -> list[dict]:
    """Return a list of recent news headlines for the ticker.

    Each item is normalized to: {title, publisher, published_at, url}.
    Silent on failure — returns [] so the news agent can degrade gracefully.
    """
    symbol = (ticker or "").strip().upper()
    if not symbol:
        return []

    try:
        raw = yfinance.Ticker(symbol).news or []
    except Exception:
        return []

    items: list[dict] = []
    for entry in raw[:limit]:
        # yfinance 1.2.x returns {"id", "content": {...}} shape.
        content = entry.get("content") if isinstance(entry, dict) else None
        if isinstance(content, dict):
            title = content.get("title")
            publisher = (content.get("provider") or {}).get("displayName")
            published_at = content.get("pubDate") or content.get("displayTime")
            url = (
                (content.get("canonicalUrl") or {}).get("url")
                or (content.get("clickThroughUrl") or {}).get("url")
            )
        else:
            # Legacy flat shape.
            title = entry.get("title")
            publisher = entry.get("publisher")
            published_at = entry.get("providerPublishTime")
            url = entry.get("link")

        if not title:
            continue
        items.append(
            {
                "title": title,
                "publisher": publisher,
                "published_at": published_at,
                "url": url,
            }
        )

    return items
