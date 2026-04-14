from typing import Annotated, TypedDict


def _last_value(_existing: object, new: object) -> object:
    # Reducer for parallel writes: fundamentals + news both set status_message
    # in the same super-step. Last write wins; per-node updates still stream
    # independently via astream(stream_mode="updates").
    return new


class ResearchState(TypedDict, total=False):
    ticker: str

    status_message: Annotated[str | None, _last_value]

    company_name: str | None
    validation_error: str | None

    fundamentals: dict | None
    fundamentals_error: str | None

    news: dict | None
    news_error: str | None

    briefing: dict | None

    error: str | None
