# Build Checklist

## Build Preferences

- **Build mode:** Step-by-step
- **Comprehension checks:** Yes, for backend/graph items (steps 2–7). Off for frontend items (familiar territory for Kamen).
- **Git:** Commit after each checklist step with message format `step N: [title]`. Clean revert points per item.
- **Verification:** Yes — per-item verification. Step-by-step requires it; skipping defeats the mode.
- **Check-in cadence:** Learning-driven. Narrate decisions as they're made, especially on LangGraph, SSE, and agent-orchestration pieces. Tailwind/boilerplate can be quieter.

**Demo tickers:** AAPL (breadth, rich fundamentals) + FIG/Figma (fresh IPO, thematic fit, strong implicit-connection material).

**Sequencing rationale:** Backend-first, inside-out. LangGraph topology and SSE pacing land early (steps 2–3) with stubs, so the risky/new learning surface is battle-tested before real LLM latency and yfinance flakiness enter the picture. Endpoints and real agents layer on top (4–7). Frontend glides onto a known-good SSE contract (8–9b). Polish + submit closes (10).

## Checklist

- [x] **1. Project scaffolding (backend + frontend skeletons)**
  Spec ref: `spec.md > File Structure`, `spec.md > Runtime & Deployment`
  What to build: Create `backend/` with `pyproject.toml` (uv). Install `fastapi`, `uvicorn[standard]`, `langgraph`, `anthropic`, `yfinance`, `pydantic`, `python-dotenv`, `sse-starlette`, `pytest`, `pytest-asyncio`. Stub `main.py` with `GET /health → {ok:true}`. Add `backend/.env.example` with `ANTHROPIC_API_KEY=`. Create `frontend/` via `pnpm create next-app@latest` (TypeScript, Tailwind, App Router, no src-dir). Add `frontend/.env.local.example` with `NEXT_PUBLIC_API_URL=http://localhost:8000`.
  Acceptance: Both servers start clean. `curl localhost:8000/health` returns `{ok:true}`. `localhost:3000` shows default Next.js page. No install errors.
  Verify: Run `uv run uvicorn main:app --reload --port 8000` in one terminal and `pnpm dev` in another. Hit both URLs in a browser or via curl.

- [x] **2. LangGraph skeleton with stub nodes + state + tests**
  Spec ref: `spec.md > LangGraph Orchestrator > State`, `spec.md > LangGraph Orchestrator > Graph Wiring`, `spec.md > Progress Strategy (Strategy C)`
  What to build: Create `backend/graph/state.py` defining `ResearchState` TypedDict per spec. Create stub node modules `backend/graph/nodes/{validate,fundamentals,news,synthesis}.py` — each writes `status_message` plus a hardcoded placeholder payload into state. Wire `backend/graph/graph.py` per spec: `START → validate → conditional_edges → [fundamentals, news] (fan-out) → synthesis → END`. Write `backend/tests/test_graph.py` that runs `compiled.astream(state, stream_mode="updates")` for a fake ticker and asserts the update sequence includes validate → fundamentals + news (both emitted) → synthesis.
  Acceptance: `pytest` is green. Graph executes end-to-end with stubs. Fan-out is visible in the update stream — both `fundamentals` and `news` updates appear between `validate` and `synthesis`.
  Verify: Run `uv run pytest -v`. Read the assertion output and confirm both parallel branches fire before synthesis.
  Comprehension check: Why does `add_conditional_edges` return a *list* `["fundamentals", "news"]` rather than two separate edges?

- [x] **3. SSE pacing wrapper + `/research` endpoint (stubbed graph)**
  Spec ref: `spec.md > Backend > /research endpoint (SSE)`, `spec.md > SSE pacing wrapper`, `spec.md > SSE Event Vocabulary`
  What to build: Implement `backend/sse.py` with a `format_sse(event, data)` helper and an async generator enforcing a 1.2s minimum gap between emitted events (per spec code snippet). Wire `POST /research` in `main.py` using `sse-starlette`'s `EventSourceResponse`, feeding the stubbed graph from step 2. Emit `progress` events keyed off each node's `status_message`. Write `backend/tests/test_sse.py` asserting (a) event format matches `event: ...\ndata: ...\n\n`, (b) two rapid updates emit ≥1.2s apart.
  Acceptance: `curl -N -X POST localhost:8000/research -H "Content-Type: application/json" -d '{"ticker":"AAPL"}'` streams `event: progress` lines paced ≥1.2s apart. Tests green.
  Verify: Run the curl command. Count seconds between lines — should feel readable, not machine-gun. Run `pytest`.
  Comprehension check: Why does pacing live in the SSE wrapper rather than inside each graph node?

- [x] **4. Real `/validate` endpoint + validate node (yfinance)**
  Spec ref: `spec.md > Backend > /validate endpoint`, `spec.md > Validate Node`
  What to build: Create `backend/clients/yfinance_client.py` — thin wrapper around `yfinance.Ticker(ticker).info`, error normalization (empty dict / missing `longName` → raises a domain error). Wire `POST /validate` synchronously: returns `{valid:true, company_name}` on success, `{valid:false, error:"We couldn't find that ticker..."}` on miss. Replace the stub validate node with the real implementation using the shared client helper. Tests: AAPL (valid), ZZZZZ (invalid), empty string (invalid).
  Acceptance: `curl -X POST localhost:8000/validate -d '{"ticker":"AAPL"}' -H "Content-Type: application/json"` → `{valid:true, company_name:"Apple Inc."}`. Same with `ZZZZZ` → `{valid:false, ...}`. Tests green.
  Verify: Run both curls. Run `pytest`.
  Comprehension check: Why does `spec.md` mandate the validate node re-run yfinance even though `/validate` already did?

- [x] **5. Fundamentals agent (real yfinance + Sonnet) + early header SSE emit**
  Spec ref: `spec.md > Fundamentals Agent`, `spec.md > SSE Event Vocabulary > header`, `prd.md > Research Results > essential company context`
  What to build: Replace fundamentals stub with real implementation — yfinance fetch, extract 6 header metrics (name, ticker, sector, price + %change, market cap, trailing P/E, 52-week range, dividend yield if present), build full `raw_metrics`, call Sonnet 4.6 with prompt from `backend/prompts/fundamentals_summary.md` (write this prompt file). Write `backend/clients/anthropic_client.py` shared SDK client + model constants. Update SSE layer to detect when `state.fundamentals.header` first appears and emit a `header` SSE event mid-stream (before synthesis finishes). Tests mock the Sonnet call; manual verify uses real call.
  Acceptance: `/research` for AAPL emits `progress` events, then a `header` SSE event mid-stream containing all 6 header metrics populated. Sonnet summary returns 2-3 paragraphs of qualitative posture. PRD "essential company context" acceptance criteria met.
  Verify: Manual curl with AAPL — confirm `header` event fires before `result` event (i.e., appears while other nodes still running). Inspect the summary prose — does it read like analyst context, not raw numbers?
  Comprehension check: The header event emits *during* the graph run, not at the end. What's the mechanism that lets the SSE layer detect it at the right moment?

- [x] **6. News agent (yfinance + Anthropic `web_search` dual-source)**
  Spec ref: `spec.md > News Agent`, `prd.md > Research Results > implicit connections`
  What to build: Replace news stub with real implementation — `yfinance.Ticker(ticker).news` for company-specific headlines, then Sonnet 4.6 call with `web_search` tool and prompt from `backend/prompts/news_analyst.md` (write this prompt file). Structured output with `direct_news`, `macro_context`, `implicit_connections` (capped 3-5 per spec). 30s soft timeout via `asyncio.wait_for` around the Anthropic call. Fallback to yfinance-only if web_search fails. Tests mock the Anthropic call and verify structure + timeout behavior.
  Acceptance: `/research` for AAPL populates `state.news` with all three fields. Implicit connections list has 3-5 non-obvious items (not just headline restatements). Web search failure degrades gracefully to yfinance-only without killing the run. PRD "implicit connections" criterion met.
  Verify: Manual curl for AAPL. Inspect the final payload — do the implicit connections actually surface non-obvious links (e.g., "EU regulation X → services revenue risk"), or are they just headlines rephrased?
  Comprehension check: Why is the `web_search` tool attached to the news agent, and not synthesis?

- [ ] **7. Synthesis agent (Opus 4.6 + `emit_briefing` tool) + final `result` SSE event**
  Spec ref: `spec.md > Synthesis Agent`, `spec.md > SSE Event Vocabulary > result`, `prd.md > Research Results > three distinct perspectives`
  What to build: Replace synthesis stub with real Opus 4.6 call. Prompt from `backend/prompts/synthesis.md` (write this prompt file). Force `emit_briefing` tool via `tool_choice`. Parse structured tool output into `Briefing` pydantic model (`backend/schemas/briefing.py` with `Citation`, `Argument`, `Briefing`). Fail-hard on upstream errors or Opus failure (no Sonnet fallback) — sets `state.error`, routes to terminal error event. Emit `result` SSE event with the briefing. Full end-to-end test with mocked LLMs covering happy path + upstream error path.
  Acceptance: `/research` for AAPL emits `result` SSE event containing `{buy, hold, sell}`, each with `summary`, `reasoning`, `confidence` (strong/moderate/thin), `citations`. PRD "three distinct perspectives" acceptance criteria met. Tests green.
  Verify: Manual curl for *both* AAPL and FIG. Read the three arguments for FIG — do they meaningfully disagree, or are they hedged mush? Confidence tags feel honest (thin when evidence is thin)?
  Comprehension check: Why does the spec insist on *one* Opus call producing all three arguments rather than three parallel Opus calls?

- [ ] **8. Frontend — landing screen (`app/page.tsx` + `TickerInput` + `/validate` wiring)**
  Spec ref: `spec.md > Frontend > Pages > Landing Screen`, `spec.md > Components > TickerInput`, `spec.md > Visual Design`, `prd.md > Ticker Input`
  What to build: Pick serif font from shortlist (Source Serif 4 / Crimson Pro / Newsreader) and load via `next/font` in `app/layout.tsx`. Set up editorial theme in `app/globals.css` — off-white background, dark slate text, one muted accent (teal or amber — pick by eye). Build `components/TickerInput.tsx`: centered input, inline loader swap on submit, soft error message below (friendly tone per PRD), error clears on next keystroke, retains entered text. Build `lib/api.ts` with `validateTicker(ticker)`. On `{valid:true}` → `router.push("/results/[ticker]")` (results page can be a placeholder for now).
  Acceptance: Landing screen renders with editorial feel (serif, light palette, generous spacing). Submitting AAPL → smooth transition to results route. Submitting ZZZZZ → soft error below input, text retained, error clears on next keystroke. All PRD Ticker Input acceptance criteria met.
  Verify: `pnpm dev`. Try AAPL (routes to results placeholder), ZZZZZ (soft error appears), start typing again (error clears). Tab through for keyboard UX.

- [ ] **9a. Frontend — SSE consumer + progress display + company header**
  Spec ref: `spec.md > Frontend > Pages > Results Screen`, `spec.md > Components > {ProgressDisplay, CompanyHeader}`, `spec.md > Lib > sse.ts`, `spec.md > Lib > types.ts`, `prd.md > Research Progress`
  What to build: `lib/types.ts` mirroring backend schemas (`Briefing`, `Argument`, `HeaderData`, `ProgressEvent`). `lib/sse.ts` wrapping `@microsoft/fetch-event-source` with `streamResearch(ticker, handlers)` exposing `{ onProgress, onHeader, onResult, onError }`. `app/results/[ticker]/page.tsx`: mount → open SSE → render anchored "loading…" header + `ProgressDisplay`. `components/ProgressDisplay.tsx` animates fade-out → fade-in on each new message via CSS transitions (no animation library). `components/CompanyHeader.tsx` renders on `header` event, replacing loading state — shows name + ticker, sector tag, price + % change, market cap, trailing P/E, 52-week range visualizer, dividend yield (if present). Editorial layout, serif headings, generous spacing.
  Acceptance: Navigating to `/results/AAPL` opens the SSE stream, progress messages fade in/out smoothly (no hard cuts), company header arrives mid-stream and replaces loading state without a jarring transition. All PRD Research Progress acceptance criteria met.
  Verify: `pnpm dev`. Enter AAPL on landing, watch the results screen — progress messages should fade (not jump), header should fade/slide in while progress is still running (confirms early-emit is working end-to-end).

- [ ] **9b. Frontend — perspective cards + error state**
  Spec ref: `spec.md > Components > {PerspectiveCards, PerspectiveCard, ErrorState}`, `prd.md > Research Results`, `prd.md > Research Progress > error handling`
  What to build: `components/PerspectiveCards.tsx` renders 3 `PerspectiveCard`s (Buy / Hold / Sell) once the `result` event arrives, fading in as `ProgressDisplay` fades out. `components/PerspectiveCard.tsx`: collapsed shows title (e.g., "The case for buying"), 2-3 sentence summary, small confidence tag ("Evidence: strong/moderate/thin"). Expanded reveals full reasoning paragraphs + citations list with links (URLs open in new tab). Smooth expand/collapse via CSS height transition. `components/ErrorState.tsx` replaces progress area on SSE `error` event — friendly message + "Back" button that smoothly routes to landing.
  Acceptance: End-to-end AAPL flow renders all three cards. Each card expands/collapses smoothly. Citations link out. Error path (e.g., killing backend mid-stream) renders `ErrorState` with working back button. All PRD Research Results + Research Progress error-handling acceptance criteria met.
  Verify: Run AAPL + FIG full flow. Click each card — confirm smooth expand/collapse, citations render as clickable links. Force an error (kill backend mid-research or point to a dead ticker) — confirm error state appears and back button returns to landing with a fade, not a hard cut.

- [ ] **10. Polish pass + demo recording + Devpost submission**
  Spec ref: `prd.md > Visual Design & Transitions`, `prd.md > What We're Building`, `prd.md > Non-Goals` (submission story)
  What to build: Final visual pass — lock serif choice, lock accent color, tighten spacing where needed, sanity-check every transition for no-hard-cuts rule. Record 60-90s screen capture (AAPL and/or FIG end-to-end flow) and upload unlisted to YouTube. Take 4 screenshots: (1) landing, (2) progress mid-stream with message visible, (3) header + three cards rendered, (4) expanded card showing reasoning + citations. Write Devpost project page: name + tagline, story (pulled from `scope.md` + `prd.md` — lead with the three-perspectives pitch, LangGraph orchestration as the learning/architecture angle, editorial design as the polish angle), built-with tags (Next.js, TypeScript, Tailwind, Python, FastAPI, LangGraph, Anthropic Sonnet/Opus, yfinance), upload screenshots, attach docs artifacts (scope, prd, spec, checklist), link the GitHub repo (remote already set), embed the YouTube video. Review and submit.
  Acceptance: Devpost submission is live with the green "Submitted" badge. All required fields complete: name, tagline, story, built-with, screenshots, repo link, video. Story reads compellingly to someone who has never seen the project.
  Verify: Open the Devpost submission page. Read the description as if you'd never seen this project before — is the three-perspectives hook clear in the first 2 sentences? Does a screenshot show the "wow moment" (implicit connection surfaced on a card)?
