import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from graph.graph import compiled
from sse import graph_events, pace_events

app = FastAPI(title="TickerLens Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    ticker: str


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/research")
async def research(req: ResearchRequest):
    initial_state = {"ticker": req.ticker.upper()}

    async def stream():
        async for event, data in pace_events(graph_events(compiled, initial_state)):
            yield {"event": event, "data": json.dumps(data)}

    return EventSourceResponse(stream())
