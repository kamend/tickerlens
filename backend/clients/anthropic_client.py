from __future__ import annotations

import os
from functools import lru_cache

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()

MODEL_SONNET = "claude-sonnet-4-6"
MODEL_OPUS = "claude-opus-4-6"


@lru_cache(maxsize=1)
def get_client() -> AsyncAnthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return AsyncAnthropic(api_key=api_key)
