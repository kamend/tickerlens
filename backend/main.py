import asyncio
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from clients.yfinance_client import TickerNotFoundError, fetch_info
from graph.graph import compiled
from sse import graph_events, pace_events

load_dotenv()

app = FastAPI(title="TickerLens Backend")

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    ticker: str


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


class ValidateRequest(BaseModel):
    ticker: str


@app.post("/validate")
async def validate(req: ValidateRequest) -> dict:
    try:
        info = await asyncio.to_thread(fetch_info, req.ticker)
    except TickerNotFoundError as exc:
        return {"valid": False, "error": exc.message}

    return {"valid": True, "company_name": info["longName"]}


@app.post("/research")
async def research(req: ResearchRequest):
    initial_state = {"ticker": req.ticker.upper()}

    async def stream():
        async for event, data in pace_events(graph_events(compiled, initial_state)):
            yield {"event": event, "data": json.dumps(data)}

    return EventSourceResponse(stream())
