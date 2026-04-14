# TickerLens — Technical Spec

## Stack

**Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind CSS. Managed with **pnpm**.
- [Next.js docs](https://nextjs.org/docs)
- [Tailwind CSS docs](https://tailwindcss.com/docs)
- [`@microsoft/fetch-event-source`](https://www.npmjs.com/package/@microsoft/fetch-event-source) — SSE client that supports POST with payload (native `EventSource` is GET-only).

**Backend:** Python 3.11+ + FastAPI + Uvicorn. Managed with **uv** (or poetry).
- [FastAPI docs](https://fastapi.tiangolo.com/)
- [FastAPI SSE tutorial](https://fastapi.tiangolo.com/tutorial/server-sent-events/)
- [SSE + FastAPI + LangGraph reference walkthrough](https://www.softgrade.org/sse-with-fastapi-react-langgraph/)

**Agent orchestration:** [LangGraph](https://github.com/langchain-ai/langgraph) (v1.0+, runtime `langgraph` 0.3.x). Stateful graph with parallel fan-out and a join node.
- [LangGraph streaming docs](https://docs.langchain.com/oss/python/langgraph/streaming) — `astream(stream_mode="updates")` is the basis of progress streaming.

**LLM:** [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python).
- **Sonnet 4.6** (`claude-sonnet-4-6`) — fundamentals summary, news/macro analyst (with `web_search` tool).
- **Opus 4.6** (`claude-opus-4-6`) — synthesis (Buy/Hold/Sell briefing).
- [Claude `web_search` tool docs](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/partner-models/claude/web-search) — same API on the Anthropic endpoint.

**Market data:** [yfinance](https://pypi.org/project/yfinance/) — free Python wrapper around Yahoo Finance.
- [yfinance docs](https://ranaroussi.github.io/yfinance/)
- ⚠️ Known issue: `ticker.financials` / `balance_sheet` / `cashflow` return empty DataFrames. We use `ticker.info` (works) and `ticker.news` (works) only.

**Rationale:** Kamen is a senior engineer (20yr) wanting to learn agent orchestration formally. LangGraph makes the orchestration topology explicit (graph nodes & edges) — perfect learning artifact. FastAPI + Next.js are familiar territory so cognitive load stays on the new thing.

## Runtime & Deployment

**Local-only.** No public deployment. Two processes run side-by-side:

- Backend: `uvicorn main:app --reload --port 8000`
- Frontend: `pnpm dev` (port 3000)

**Environment requirements:**
- Python 3.11+
- Node 20+ (for Next.js 15)
- pnpm
- `ANTHROPIC_API_KEY` in `backend/.env`

**Demo:** Recorded screen capture for Devpost submission. No public URL — Kamen explicitly wants to avoid burning tokens on random traffic.

## Architecture Overview

```
┌─────────────────────┐         POST /validate {ticker}        ┌──────────────────────┐
│   Next.js (App)     │ ─────────────────────────────────────▶ │   FastAPI Backend    │
│                     │ ◀── { valid: bool, company_name? } ── │                      │
│  - Landing screen   │                                        │  - /validate         │
│  - Results screen   │         POST /research {ticker}        │  - /research (SSE)   │
│  - Three cards      │ ─────────────────────────────────────▶ │                      │
│                     │ ◀── SSE: progress / header / result / error                  │
└─────────────────────┘                                        └──────────┬───────────┘
                                                                          │
                                                              compiled.astream(state)
                                                                          │
                                                                          ▼
                                                        ┌────────────────────────────────┐
                                                        │      LangGraph Orchestrator    │
                                                        │                                │
                                                        │   [validate]                   │
                                                        │       │                        │
                                                        │       ▼                        │
                                                        │   ┌─ fan-out ─┐                │
                                                        │   ▼           ▼                │
                                                        │ [fundamentals]  [news]         │
                                                        │   │           │                │
                                                        │   └─── join ──┘                │
                                                        │       ▼                        │
                                                        │   [synthesis]                  │
                                                        │       │                        │
                                                        │       ▼                        │
                                                        │   { buy, hold, sell }          │
                                                        └────────────────────────────────┘
```

**Data flow — lifecycle of one ticker:**

```
1. User types "AAPL" → Enter
2. Frontend POST /validate → backend yfinance lookup → { valid:true, company_name:"Apple Inc." }
3. Frontend route push to /results/AAPL
4. Results page opens SSE: POST /research {ticker:"AAPL"}
5. Backend runs graph.astream():
     [validate] → emit progress "Looking up AAPL..."
     [fan-out: fundamentals + news in parallel]
       [fundamentals] → emit progress "Reading Apple's fundamentals..."
                      → yfinance.info → header + raw_metrics
                      → Sonnet call → summary prose
                      → emit "header" event (UI anchors company header EARLY)
       [news]         → emit progress "Scanning recent news..."
                      → yfinance.news + Sonnet w/ web_search
                      → direct_news + macro_context + implicit_connections
     [join]
     [synthesis]      → emit progress "Building the case for each perspective..."
                      → Opus call w/ emit_briefing tool → { buy, hold, sell, confidence }
6. Backend emits final `result` event → SSE closes
7. Frontend fades progress out, fades header (already there) + 3 cards in
8. User clicks card → expands with reasoning + citations + confidence tag
```

## Backend — FastAPI Application

Implements `prd.md > Ticker Input` and `prd.md > Research Progress`.

### `/validate` endpoint

- **Method:** POST
- **Path:** `/validate`
- **Request:** `{ "ticker": "AAPL" }`
- **Response (200):** `{ "valid": true, "company_name": "Apple Inc." }`
- **Response (200, invalid):** `{ "valid": false, "error": "We couldn't find that ticker..." }`
- **Behavior:** Synchronous. Calls `yfinance.Ticker(ticker).info` — if `longName` is missing or the dict is empty, returns `valid: false`. Used by the frontend before transitioning to `/results/[ticker]`.
- **Implements:** `prd.md > Ticker Input` validation acceptance criteria.

### `/research` endpoint (SSE)

- **Method:** POST
- **Path:** `/research`
- **Request:** `{ "ticker": "AAPL" }`
- **Response:** `text/event-stream` (Server-Sent Events) with the event vocabulary below.
- **Behavior:** Builds initial `ResearchState`, calls `compiled_graph.astream(state, stream_mode="updates")`, wraps the iterator in an SSE pacing layer (1.2s minimum display per progress message), yields events as they arrive.

### SSE Event Vocabulary

The contract between backend and frontend.

```typescript
// Progress — agent has started a phase
{ event: "progress", data: { node: "fundamentals", message: "Reading Apple's fundamentals..." } }

// Header — emitted as soon as fundamentals.header is ready, so UI renders the company header
// EARLY while synthesis is still running. Premium UX touch.
{ event: "header", data: {
    company_name: "Apple Inc.",
    ticker: "AAPL",
    sector: "Technology",
    price: 178.42,
    metrics: { market_cap, pe_trailing, fifty_two_week, dividend_yield, change_pct }
}}

// Result — final briefing, stream ends after this
{ event: "result", data: { buy: {...}, hold: {...}, sell: {...} } }

// Error — any node failure; stream ends after this
{ event: "error", data: { message: "We couldn't complete research for AAPL." } }
```

### SSE pacing wrapper (`backend/sse.py`)

Enforces a minimum display time per progress message so users actually read each one (Raycast-style craft detail). Lives on the backend so the frontend stays a dumb renderer.

```python
MIN_MESSAGE_DISPLAY = 1.2  # seconds
last_emit = time.monotonic()
async for event in compiled.astream(initial_state, stream_mode="updates"):
    elapsed = time.monotonic() - last_emit
    if elapsed < MIN_MESSAGE_DISPLAY:
        await asyncio.sleep(MIN_MESSAGE_DISPLAY - elapsed)
    yield format_sse(event)
    last_emit = time.monotonic()
```

## LangGraph Orchestrator

Implements `prd.md > Research Progress` and feeds `prd.md > Research Results`.

### State (`backend/graph/state.py`)

```python
class ResearchState(TypedDict):
    # Input
    ticker: str

    # Per-node first-action: a user-friendly progress message
    status_message: str | None

    # Populated by validate node
    company_name: str | None
    validation_error: str | None

    # Populated by fundamentals_agent (parallel branch A)
    fundamentals: dict | None
    fundamentals_error: str | None

    # Populated by news_agent (parallel branch B)
    news: dict | None
    news_error: str | None

    # Populated by synthesis_agent
    briefing: dict | None

    # Terminal
    error: str | None
```

### Graph Wiring (`backend/graph/graph.py`)

```python
graph = StateGraph(ResearchState)
graph.add_node("validate",     validate_ticker_node)
graph.add_node("fundamentals", fundamentals_agent_node)
graph.add_node("news",         news_agent_node)
graph.add_node("synthesis",    synthesis_agent_node)

graph.add_edge(START, "validate")

# Conditional: invalid ticker → END; valid → fan out to both branches
graph.add_conditional_edges(
    "validate",
    lambda s: "error" if s["validation_error"] else "gather",
    { "error": END, "gather": ["fundamentals", "news"] }
)

# Both must complete before synthesis (LangGraph join)
graph.add_edge("fundamentals", "synthesis")
graph.add_edge("news",         "synthesis")

graph.add_edge("synthesis", END)
compiled = graph.compile()
```

### Progress Strategy (Strategy C)

Each node's **first action** is to write `state["status_message"] = "..."`. LangGraph's `astream(stream_mode="updates")` then emits this update *before* the heavy work begins, so the user sees "Reading Apple's fundamentals..." as the work starts (not after it finishes).

This keeps progress messaging genuinely backend-driven — no UI guessing.

### Validate Node (`backend/graph/nodes/validate.py`)

- Calls `yfinance.Ticker(ticker).info`.
- If `longName` exists → writes `company_name`.
- If empty/missing → writes `validation_error`.
- ~5ms typical. Defense-in-depth even though `/validate` endpoint also runs this.
- **Implements:** backstop for `prd.md > Ticker Input`.

### Fundamentals Agent (`backend/graph/nodes/fundamentals.py`)

**Implements:** `prd.md > Research Results > essential company context` (header) and feeds synthesis.

```
1. Write status_message = "Reading {company_name}'s fundamentals..."
2. yfinance.Ticker(ticker).info  (deterministic fetch)
3. Extract header metrics:
     - longName, symbol, sector
     - currentPrice, previousClose (compute % change)
     - fiftyTwoWeekHigh, fiftyTwoWeekLow
     - marketCap
     - trailingPE
     - dividendYield (if present)
4. Build raw_metrics: above + forwardPE, priceToBook, profitMargins,
   returnOnEquity, debtToEquity, revenueGrowth, earningsGrowth,
   longBusinessSummary
5. Sonnet 4.6 call with prompt @ prompts/fundamentals_summary.md
   Input: raw_metrics as JSON
   Output: 2-3 paragraph qualitative summary of the company's
           current fundamental posture
6. Write to state.fundamentals = { header, raw_metrics, summary }
7. EMIT header event (handled by SSE wrapper picking up the
   fundamentals.header field as it appears in state)
```

**Failure handling:** If `ticker.info` empty or LLM call fails → `state["fundamentals_error"]`. Synthesis node sees this and routes to error terminal.

### News Agent (`backend/graph/nodes/news.py`)

**Implements:** `prd.md > Research Results > Buy/Hold/Sell arguments grounded in current news` (the news-half).

**Dual-source strategy** for resilience and freshness.

```
1. Write status_message = "Scanning recent news and macro context..."
2. yfinance.Ticker(ticker).news  →  list of recent headlines
   (title, publisher, providerPublishTime, link)
3. Sonnet 4.6 call with prompt @ prompts/news_analyst.md
   Tools: [web_search]
   Input: { ticker, company_name, sector, yfinance_headlines }
   Constraint: surface MAX 3-5 implicit connections
   Soft timeout: 30s (configured at the Anthropic client level)
   Output (structured tool call):
     {
       direct_news: [ {title, publisher, date, url, our_note} ],
       macro_context: [ {topic, summary, source_urls} ],
       implicit_connections: [ "EU regulation X → services revenue risk", ... ]
     }
4. Write to state.news = { ... }
```

**Failure handling:**
- If web_search fails → fall back to yfinance-only news (still continue).
- If yfinance also empty → set `state["news_error"]`. Synthesis routes to error.

### Synthesis Agent (`backend/graph/nodes/synthesis.py`)

**Implements:** `prd.md > Research Results > three distinct perspectives Buy/Hold/Sell`.

The heart of the app. **Single Opus 4.6 call** producing all three arguments in one structured response — guarantees internal consistency and meaningful disagreement between the cases.

```
1. Check for upstream errors (fundamentals_error or news_error) → set state.error, END.
2. Write status_message = "Building the case for each perspective..."
3. Opus 4.6 call with prompt @ prompts/synthesis.md
   Tools: [emit_briefing]  (forced via tool_choice)
   Input:
     - ticker, company_name
     - fundamentals.summary + fundamentals.raw_metrics
     - news.direct_news + news.macro_context + news.implicit_connections
4. Receive structured tool call with the briefing
5. Write to state.briefing = { buy, hold, sell }
```

**Tool schema (`emit_briefing`):**

```json
{
  "name": "emit_briefing",
  "description": "Emit the final Buy/Hold/Sell briefing for the investor.",
  "input_schema": {
    "type": "object",
    "required": ["buy", "hold", "sell"],
    "properties": {
      "buy":  { "$ref": "#/$defs/argument" },
      "hold": { "$ref": "#/$defs/argument" },
      "sell": { "$ref": "#/$defs/argument" }
    },
    "$defs": {
      "argument": {
        "type": "object",
        "required": ["summary", "reasoning", "confidence", "citations"],
        "properties": {
          "summary":     { "type": "string", "description": "2-3 sentence collapsed-card summary" },
          "reasoning":   { "type": "string", "description": "3-5 paragraphs of full reasoning" },
          "confidence":  { "type": "string", "enum": ["strong", "moderate", "thin"] },
          "citations":   { "type": "array", "items": {
                            "type": "object",
                            "required": ["title", "url"],
                            "properties": {
                              "title": { "type": "string" },
                              "url":   { "type": "string" }
                            }
                          }}
        }
      }
    }
  }
}
```

**Failure handling:** Fail hard. No Sonnet fallback (would silently degrade UX). If Opus call fails → `state["error"]` → SSE error event → frontend shows error state with back button.

### Prompts (`backend/prompts/*.md`)

Stored as separate `.md` files for editability without touching code, and so iteration on prompts produces readable diffs.

- `fundamentals_summary.md` — instructs Sonnet to write a qualitative posture summary from raw metrics.
- `news_analyst.md` — instructs Sonnet to combine yfinance headlines with web_search to surface 3-5 implicit connections.
- `synthesis.md` — instructs Opus to produce three internally-consistent, meaningfully-disagreeing arguments with confidence ratings, calling `emit_briefing`.

## Frontend — Next.js App

### Pages

#### `app/page.tsx` — Landing Screen

**Implements:** `prd.md > Ticker Input`, `prd.md > Visual Design & Transitions`.

- Centered ticker input field (`TickerInput` component).
- On submit: POST `/validate`, show inline loader.
- Invalid → soft error message under input, retain text.
- Valid → smooth transition (`router.push("/results/[ticker]")`).
- Editorial light palette, serif typography.

#### `app/results/[ticker]/page.tsx` — Results Screen

**Implements:** `prd.md > Research Progress`, `prd.md > Research Results`.

- On mount: open SSE to POST `/research { ticker }` via `lib/sse.ts`.
- Initial render: anchored "loading…" header + `ProgressDisplay`.
- On `progress` event → update `ProgressDisplay`.
- On `header` event → render `CompanyHeader` (anchored top, replaces loading state).
- On `result` event → fade out progress, fade in `PerspectiveCards`.
- On `error` event → render `ErrorState` with back button.

### Components

#### `components/TickerInput.tsx`
Input field, inline submit/loader swap, soft error message. Disappears error on next keystroke.

#### `components/ProgressDisplay.tsx`
Animated text — fade-out current message, fade-in next. Uses CSS transitions (no animation library needed).

#### `components/CompanyHeader.tsx`
Renders early when `header` SSE event arrives. Shows: company name + ticker, sector tag, current price + % change, market cap, trailing P/E, 52-week range visualizer, dividend yield (if present). Editorial layout — generous spacing, serif headings.

#### `components/PerspectiveCards.tsx` + `PerspectiveCard.tsx`
Three cards: Buy / Hold / Sell. Each:
- Collapsed: title (e.g., "The case for buying"), 2-3 sentence summary, small confidence tag ("Evidence: strong / moderate / thin").
- Expanded: full reasoning paragraphs + citation list with links.
- Smooth expand/collapse animation (CSS height transition or Framer Motion if needed).

#### `components/ErrorState.tsx`
Replaces progress area on error. Friendly message + "Back" button → smooth transition to landing.

### Lib

#### `lib/api.ts`
`validateTicker(ticker)` → POST `/validate`.

#### `lib/sse.ts`
Wraps `@microsoft/fetch-event-source`. Exposes `streamResearch(ticker, handlers)` where handlers = `{ onProgress, onHeader, onResult, onError }`.

#### `lib/types.ts`
TypeScript mirrors of backend pydantic schemas: `Briefing`, `Argument`, `HeaderData`, `ProgressEvent`.

### Visual Design

**Implements:** `prd.md > Visual Design & Transitions`.

- **Palette:** Light. Off-white background (#FAFAF7 or similar warm neutral), dark slate text (#1F2024), one accent for interactive elements (a muted teal or amber — final pick during build).
- **Typography:** Serif for headings and body (candidates: [Source Serif 4](https://fonts.google.com/specimen/Source+Serif+4), [Crimson Pro](https://fonts.google.com/specimen/Crimson+Pro), [Newsreader](https://fonts.google.com/specimen/Newsreader)). Sans-serif (system or Inter) only for small UI labels and metric numbers.
- **Spacing:** Generous. Card padding `p-8`. Section gaps `gap-12`. Editorial breathing room.
- **Transitions:** Tailwind transitions or CSS keyframes. All view-state changes use 250-400ms fade/slide. No hard cuts.
- **No dark mode.**

## Data Model

### `ResearchState` (LangGraph)

See [State](#state-backendgraphstatepy) above.

### `Briefing` (final synthesis output)

```python
class Citation(BaseModel):
    title: str
    url: str

class Argument(BaseModel):
    summary: str           # 2-3 sentences (collapsed card)
    reasoning: str         # 3-5 paragraphs (expanded card)
    confidence: Literal["strong", "moderate", "thin"]
    citations: list[Citation]

class Briefing(BaseModel):
    buy: Argument
    hold: Argument
    sell: Argument
```

### `HeaderData` (early-emit payload)

```python
class HeaderMetrics(BaseModel):
    market_cap: int
    pe_trailing: float | None
    fifty_two_week_low: float
    fifty_two_week_high: float
    dividend_yield: float | None
    change_pct: float

class HeaderData(BaseModel):
    company_name: str
    ticker: str
    sector: str
    price: float
    metrics: HeaderMetrics
```

## File Structure

```
tickerlens/
├── README.md
├── .env.example                      # ANTHROPIC_API_KEY placeholder
│
├── docs/                             # Hackathon artifacts
│   ├── learner-profile.md
│   ├── scope.md
│   ├── prd.md
│   └── spec.md                       # this file
├── process-notes.md
│
├── backend/
│   ├── pyproject.toml                # uv/poetry project
│   ├── .env                          # gitignored — ANTHROPIC_API_KEY
│   ├── main.py                       # FastAPI app, mounts /validate + /research
│   ├── sse.py                        # SSE event formatter + 1.2s pacing wrapper
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py                  # ResearchState TypedDict
│   │   ├── graph.py                  # build_graph() — wires nodes, returns compiled graph
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── validate.py           # yfinance lookup, validation_error if fails
│   │       ├── fundamentals.py       # yfinance fetch + Sonnet summary call
│   │       ├── news.py               # yfinance.news + Sonnet w/ web_search
│   │       └── synthesis.py          # Opus call with emit_briefing tool
│   │
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── anthropic_client.py       # shared Claude SDK client + model constants
│   │   └── yfinance_client.py        # thin wrapper, error normalization
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── fundamentals.py           # pydantic: HeaderMetrics, FundamentalsOutput
│   │   ├── news.py                   # pydantic: NewsItem, MacroConnection, NewsOutput
│   │   └── briefing.py               # pydantic: Argument, Briefing
│   │
│   └── prompts/
│       ├── fundamentals_summary.md   # prompt text: qualitative posture from metrics
│       ├── news_analyst.md           # prompt text: dual-source + 3-5 implicit connections
│       └── synthesis.md              # prompt text: three internally-consistent arguments
│
└── frontend/
    ├── package.json                  # pnpm
    ├── pnpm-lock.yaml
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── postcss.config.js
    ├── .env.local                    # NEXT_PUBLIC_API_URL=http://localhost:8000
    │
    ├── app/
    │   ├── layout.tsx                # root layout, serif font setup, metadata
    │   ├── page.tsx                  # landing screen (TickerInput)
    │   ├── globals.css               # tailwind directives + editorial theme vars
    │   └── results/
    │       └── [ticker]/
    │           └── page.tsx          # results screen (progress → header → cards)
    │
    ├── components/
    │   ├── TickerInput.tsx           # input + inline loader + soft error
    │   ├── ProgressDisplay.tsx       # animated agent progress messages
    │   ├── CompanyHeader.tsx         # name, ticker, price, 6 metrics
    │   ├── PerspectiveCards.tsx      # the 3-card layout
    │   ├── PerspectiveCard.tsx       # collapsed/expanded, confidence tag
    │   └── ErrorState.tsx            # error message + back button
    │
    ├── lib/
    │   ├── api.ts                    # fetch wrapper for /validate
    │   ├── sse.ts                    # SSE client (@microsoft/fetch-event-source)
    │   └── types.ts                  # TS mirrors of backend pydantic schemas
    │
    └── styles/
        └── fonts.ts                  # next/font — serif choice
```

## Key Technical Decisions

### 1. LangGraph for orchestration (vs. hand-rolled or Claude Agent SDK)

**Decision:** LangGraph 1.0+ with explicit state, nodes, and parallel fan-out.
**Why:** Kamen's stated learning goal is agent orchestration. LangGraph makes the topology a first-class artifact (graph wiring is the spec). The parallel fan-out + join pattern is built-in — no manual `asyncio.gather`.
**Tradeoff accepted:** A framework layer between Kamen's code and the model. Acceptable because the framework's value (graph topology, streaming, parallel orchestration) is exactly what's being learned.

### 2. Single synthesis call (vs. three parallel argument calls)

**Decision:** One Opus 4.6 call producing all three arguments via structured tool output.
**Why:** Coherence — the model weighs the same evidence three ways in one context window, so cases meaningfully disagree without contradicting. Cheaper too (one input, three outputs).
**Tradeoff accepted:** Each argument gets less "airtime" than if it had its own dedicated call. Mitigated by the prompt explicitly demanding distinct, meaningful disagreement and by Opus's reasoning depth.

### 3. SSE with backend-paced messages (Strategy C + 1.2s minimum display)

**Decision:** Each LangGraph node writes `status_message` as its first action. Backend SSE wrapper enforces 1.2s minimum between progress events.
**Why:** Honest backend-driven messaging (no UI lying about what's running). Pacing on the backend keeps the UI a pure renderer — matches Kamen's "less business logic on UI" preference. The minimum-display time prevents fast-completing nodes from flashing past unread (Raycast-style craft).
**Tradeoff accepted:** Slight latency added when nodes complete fast (worst case ~3.6s of artificial pacing across 3 progress events). Worth it for the polish.

### 4. yfinance + Anthropic web_search dual-source for news

**Decision:** Always pull yfinance.news for company-specific headlines, AND give the news agent the `web_search` tool for macro/regulatory scanning. Cap implicit connections at 3-5.
**Why:** yfinance gives guaranteed-fresh source URLs even if web_search is flaky. web_search surfaces the implicit connections the PRD calls out (the magic). Cap keeps tokens + latency under control for a hackathon demo.
**Tradeoff accepted:** Two API calls per news node (one yfinance, one Claude). Acceptable — both are fast.

### 5. Local-only deployment

**Decision:** No public URL. Local dev for demo, screen recording for Devpost.
**Why:** Kamen explicitly wants to avoid burning tokens on random traffic. Demo via recording is standard Devpost practice and removes deploy-config overhead.
**Tradeoff accepted:** No live demo link in submission. Mitigated by a polished screen recording.

## Dependencies & External Services

### External Services

| Service | Purpose | Auth | Cost / Limits |
|---|---|---|---|
| [Anthropic API](https://docs.anthropic.com/) | Sonnet 4.6 (fundamentals, news), Opus 4.6 (synthesis), `web_search` tool | `ANTHROPIC_API_KEY` env var | Per-token usage. `web_search` tool has its own per-search pricing. Local-only deployment caps total cost. |
| [Yahoo Finance via yfinance](https://pypi.org/project/yfinance/) | `Ticker.info` (fundamentals), `Ticker.news` (headlines) | None | Free. Unofficial — can rate-limit or break without notice. ⚠️ `financials`/`balance_sheet`/`cashflow` methods broken — do NOT use. |

### Backend Python Dependencies

- `fastapi` — web framework
- `uvicorn[standard]` — ASGI server
- `langgraph` (1.0+) — orchestration
- `langchain-anthropic` — LangGraph ↔ Anthropic adapter (only if needed; we may use the raw `anthropic` SDK directly inside nodes)
- `anthropic` — Claude SDK
- `yfinance` — Yahoo Finance wrapper
- `pydantic` — schemas
- `python-dotenv` — env loading
- `sse-starlette` — `EventSourceResponse` for FastAPI

### Frontend Node Dependencies

- `next` (15+)
- `react` (19+)
- `typescript`
- `tailwindcss`
- `@microsoft/fetch-event-source` — SSE client supporting POST
- `next/font` — serif loading

### Documentation References (for build phase)

- [LangGraph quickstart](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
- [LangGraph streaming](https://docs.langchain.com/oss/python/langgraph/streaming)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Anthropic web_search tool](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/partner-models/claude/web-search)
- [Anthropic tool use (for `emit_briefing`)](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [yfinance Ticker reference](https://ranaroussi.github.io/yfinance/reference/yfinance.ticker_tickers.html)
- [FastAPI SSE](https://fastapi.tiangolo.com/tutorial/server-sent-events/)
- [`@microsoft/fetch-event-source`](https://www.npmjs.com/package/@microsoft/fetch-event-source)
- [Next.js App Router](https://nextjs.org/docs/app)
- [next/font](https://nextjs.org/docs/app/api-reference/components/font)

## Open Issues

### Resolved during /spec
- ✅ **PRD open Q1 — which fundamental metrics in the header.** Decided: company name, ticker, sector, current price + % change, market cap, trailing P/E, 52-week range visualizer, dividend yield (if present). 6 metrics max.

### Deferred (will resolve during /build)
- **PRD open Q2 — source link presentation.** Inline citations vs. reference list still open. The synthesis tool schema currently emits a `citations` array per argument, leaving room for either presentation. Decide once real briefing output is visible.
- **PRD open Q3 — tickers with very limited data.** Current behavior: if `ticker.info` is empty → `validation_error`; if news is empty but fundamentals are not → continue with news-light arguments. Edge cases (e.g., partial data, very thin headlines) might need finer handling discovered during build.

### Surfaced during /spec
- **Serif font final choice.** Three candidates noted (Source Serif 4, Crimson Pro, Newsreader). Pick during build by eye.
- **Accent color final pick.** Muted teal vs. amber — decide against real component states.
- **`langchain-anthropic` vs. raw `anthropic` inside nodes.** The LangGraph adapter is convenient but adds a dependency. Tentatively planning to use the raw `anthropic` SDK directly for full control over `web_search` tool config and structured tool calls. Re-evaluate if it complicates wiring.
- **News agent timeout enforcement.** The 30s soft timeout is conceptual — needs implementation via `asyncio.wait_for` around the Anthropic call. Confirm Anthropic SDK respects cancellation cleanly.
