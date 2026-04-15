# TickerLens

**Three perspectives on any ticker.**

TickerLens is a calm, editorially-designed financial research tool. Enter a stock ticker and you get back three reasoned perspectives — the case for buying, holding, and selling — each grounded in real fundamentals, current news, and the kind of implicit connections most tools miss.

Not a trading terminal. Not a single buy/sell signal. An analyst note that argues with itself, so you can make your own call.

---

## What it does

- **Header** — company name, price, market cap, trailing P/E, 52-week range, dividend yield. Enough to orient, not enough to overwhelm.
- **Three perspective cards** — Buy, Hold, Sell. Each a 2-3 sentence summary with a confidence tag (strong / moderate / thin), expandable into full reasoning and linked sources.
- **Implicit connections** — not "Apple reported earnings," but "new EU digital-payments regulation threatens Services margin just as hardware cost pressure is rising."

## How it works

A small multi-agent system orchestrated with **LangGraph**:

```
START → validate → ┬─ fundamentals (Sonnet 4.6) ─┐
                   └─ news (Sonnet 4.6 + web_search) ─┼→ synthesis (Opus 4.6) → END
```

- **Validate** — confirms the ticker exists via yfinance before any LLM spend.
- **Fundamentals agent** — pulls yfinance data, builds header metrics, writes an editorial posture summary with Claude Sonnet 4.6. The header is emitted *mid-stream* via LangGraph's custom stream channel so the UI fills in while news is still working.
- **News agent** — yfinance headlines + Anthropic's `web_search` tool (Sonnet 4.6) for macro context and implicit connections. Falls back to yfinance-only if search fails.
- **Synthesis agent** — Claude Opus 4.6 reads both dossiers and produces all three arguments in a single call, using a forced `emit_briefing` tool for structured output. One call so the cases can coherently *disagree*.
- **Streaming** — Server-Sent Events over FastAPI with a pacing wrapper (≥1.2s between progress messages) so the UI feels considered, not machine-gun.

## Tech stack

**Backend:** Python 3.11+, FastAPI, LangGraph, Anthropic SDK (Claude Opus 4.6 + Sonnet 4.6), yfinance, Pydantic, `sse-starlette`, uv.

**Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, `@microsoft/fetch-event-source`, Source Serif 4 + Inter via `next/font`.

---

## Install & run

### Prerequisites

- **Python** 3.11–3.13
- **[uv](https://docs.astral.sh/uv/)** (Python package manager)
- **Node.js** 20+
- **pnpm**
- An **Anthropic API key**

### 1. Clone

```bash
git clone https://github.com/kamend/tickerlens.git
cd tickerlens
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...

uv sync
uv run uvicorn main:app --reload --port 8000
```

Backend runs on `http://localhost:8000`. Sanity check:

```bash
curl http://localhost:8000/health
# {"ok":true}
```

### 3. Frontend

In a second terminal:

```bash
cd frontend
cp .env.local.example .env.local
# default points to http://localhost:8000 — edit only if you changed the backend port

pnpm install
pnpm dev
```

Open **http://localhost:3000** and enter a ticker.

---

## Usage

- Type any valid stock ticker (e.g. `AAPL`, `FIG`, `TSLA`, `GOOG`). Press Enter.
- Watch the progress messages cross-fade as the agents work.
- The company header arrives mid-stream; the three perspective cards appear when synthesis completes (typically 60-90s on a cold run — `web_search` is the slow part).
- Click any card to expand reasoning and view sources.

## Project structure

```
backend/
  main.py                    # FastAPI app + /health, /validate, /research
  sse.py                     # SSE pacing wrapper + event formatters
  graph/
    state.py                 # ResearchState TypedDict
    graph.py                 # LangGraph wiring
    nodes/                   # validate, fundamentals, news, synthesis
  clients/                   # yfinance + anthropic shared clients
  prompts/                   # fundamentals_summary / news_analyst / synthesis prompts
  schemas/briefing.py        # Pydantic: Citation, Argument, Briefing
  tests/                     # pytest suite
frontend/
  app/
    page.tsx                 # landing
    results/[ticker]/page.tsx
    layout.tsx globals.css
  components/                # TickerInput, CompanyHeader, ProgressDisplay,
                             # PerspectiveCard(s), ErrorState, ResultsView
  lib/                       # api.ts, sse.ts, types.ts
docs/                        # scope, PRD, spec, checklist, learner profile
```

## API surface

| Method | Path         | Purpose                                            |
| ------ | ------------ | -------------------------------------------------- |
| GET    | `/health`    | Liveness — returns `{ok: true}`                    |
| POST   | `/validate`  | Sync — confirms a ticker exists, returns name      |
| POST   | `/research`  | SSE — streams `progress` / `header` / `result` / `error` events |

## Tests

```bash
cd backend
uv run pytest -v
```

## Notes & known quirks

- **Cold runs take time.** `web_search` + Sonnet reasoning on a rich ticker can run 60-90s. This is intentional — the pacing wrapper and mid-stream header emit keep the UI alive during the wait.
- **yfinance flakiness.** Occasional empty `info` responses; the validate node + news fallback handle this gracefully.
- **Not financial advice.** TickerLens is a research tool for informed self-directed investors. Read the three cases, weigh the evidence, make your own call.

## License

MIT (or your preference — add a `LICENSE` file).
