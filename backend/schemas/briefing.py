from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    title: str
    url: str


class Argument(BaseModel):
    summary: str
    reasoning: str
    confidence: Literal["strong", "moderate", "thin"]
    citations: list[Citation] = Field(default_factory=list)


class Briefing(BaseModel):
    buy: Argument
    hold: Argument
    sell: Argument
