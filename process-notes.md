# Process Notes

## /onboard
- **Technical experience:** Senior engineer, 20 years across web, games, VR/AR. Currently Python, C#/Unity, React/TS, Anthropic SDK, LangChain. Has built MCP servers and chatbots.
- **Learning goals:** Agent orchestration — wants to move from building individual AI components to coordinating multi-agent systems.
- **Creative sensibility:** Appreciates slick, polished tools (Raycast/Glaze). Puzzle game fan (point-and-click, Wordle). House music DJ for 15+ years — values flow, transitions, craft.
- **Prior SDD experience:** Strong informal practice — pen-and-paper game design, Miro for architecture, Claude Code for planning. Already does this instuitively, just hasn't formalized it.
- **Background context:** Career spans multiple domains, currently fully immersed in the AI wave. Not just following — actively building and experimenting.
- **Energy and engagement:** Confident, direct, knows what he wants to learn. Moves fast. Calibrate for a senior engineer who wants depth, not hand-holding.

## /scope
- **Idea evolution:** Started as a vague "financial research chatbot," then narrowed to portfolio analysis + risk, then sharpened to "enter a ticker, get a buy/not recommendation." Final pivot: instead of the app deciding buy/sell, it presents the case for all three (Buy/Hold/Sell) and lets the user decide. This was the learner's own insight — a significant upgrade to the concept.
- **Pushback received:** Challenged on scope — portfolio tracking, multi-stock, risk analysis all cut. Kamen accepted the cuts pragmatically ("it's fair to make it simpler given the timeframe") without resistance. Also pushed on data sources — acknowledged real data matters but agreed to scope to what's wirable in 3-4 hours.
- **References that resonated:** Incite AI resonated most — right depth, wrong presentation. Kamen immediately critiqued the cluttered UI. VectorVest's clear signal structure influenced the three-card layout. WarrenAI was dismissed as "just a chatbot with general information."
- **Design direction:** Kamen drove this strongly — rejected dark mode as "overused in financial apps," chose light/calm/serif/editorial. Drew on his Raycast/Glaze aesthetic. The "analyst note, not Bloomberg terminal" framing captured his vision.
- **Deepening rounds:** 0 explicit deepening rounds chosen — the learner opted to lock in after mandatory questions. The conversation was rich enough through the mandatory flow that the scope doc had strong material.
- **Active shaping:** High. Kamen drove multiple key decisions: the three-perspectives model (instead of a single recommendation), the editorial design direction, the light mode choice, the expandable cards UX. The implicit news connections angle was his from the start. He pushed back on generic chatbot framing early and consistently moved toward something with real opinion and craft.

## /prd
- **Scope changes from scope doc:** Kamen added a two-stage validation flow (inline validation on input screen → transition to results screen only on success → separate error handling for agent failures). This wasn't in the scope doc and shows strong UX thinking — distinguishing "bad input" from "backend failure" with different UI responses.
- **What surprised them:** Nothing dramatically surprised Kamen — he's experienced enough to anticipate most edge cases. The caching complexity was a self-catch: he proposed recent tickers caching, then proactively flagged it as potentially too complex for the timeframe and agreed to defer it.
- **Scope guard:** Caching (last 5 tickers with same-day invalidation) was moved to "What we'd add with more time." Kamen initiated this himself — recognized the persistence/timestamp logic would eat into build time. Clean decision, no resistance.
- **Design convictions:** Smooth transitions between all states was a strong requirement — "I don't want raw cuts." Consistent with his DJ sensibility and Raycast/Glaze aesthetic. Also insisted on user-friendly agent progress messages ("Reading Apple's latest earnings...") rather than technical logs.
- **Deferred decisions:** Source link format (inline vs. reference list) deliberately left open — Kamen wants to see real data before deciding. Pragmatic call.
- **Deepening rounds:** 0 rounds. Kamen opted to proceed after mandatory questions. The conversation was efficient — he gave clear, decisive answers and the core flow was well-defined without needing additional probing.
- **Active shaping:** High. Kamen designed the two-stage error handling flow on the spot, self-regulated scope by flagging caching complexity, and made clear aesthetic calls (smooth transitions, friendly progress text). Asked for help researching fundamentals — knows when to delegate domain knowledge he doesn't have. Overall: decisive, scope-aware, design-driven.

## /spec
- **Stack chosen:** Next.js 15 + Tailwind (pnpm), FastAPI + Python 3.11, LangGraph 1.0+ for orchestration, Anthropic SDK direct (Sonnet 4.6 for fundamentals + news, Opus 4.6 for synthesis), yfinance for market data. Kamen drove the LangGraph choice — explicitly wants to learn it.
- **Deployment:** Local-only. Kamen flagged token-burn concerns with public deployment unprompted — strong cost-awareness instinct.
- **Architecture decisions made by Kamen:**
  - LangGraph over hand-rolled or Claude Agent SDK (learning goal-driven)
  - Single synthesis call producing all three arguments (chose coherence over per-argument depth)
  - Two endpoints (`/validate` + `/research`) over single endpoint
  - Fundamentals agent upgraded from deterministic-only to LLM-summary call ("more interesting")
  - Dual-source news (yfinance + web_search) with 3-5 implicit connection cap
  - Opus for synthesis, Sonnet for news — explicit cost/quality split
  - Fail hard on synthesis failure (no Sonnet fallback) — chose UX honesty over demo robustness
  - Confidence indicator per card ("strong/moderate/thin")
  - Strategy C for progress messages (each node writes status_message as first action) — explicit "less business logic on UI" preference
  - 1.2s artificial minimum display time for progress messages, enforced backend-side
  - Monorepo, early header SSE emit, prompts as `.md` files for editability
- **Confident on:** Stack choices, two-endpoint shape, fail-hard policy, monorepo, prompt-files-as-markdown, cost awareness throughout.
- **Uncertain on:** Will likely iterate on which fundamental metrics to display ("I will probably add different metrics and data at later stage, but I want to start somewhere"). Pragmatic — happy to ship v1 and refine.
- **Deepening rounds:** 0 chosen. Kamen opted for option A (proceed to spec) after Phase 1 mandatory questions — matches the pattern from /scope and /prd. Rich Phase 1 conversation gave the spec strong material without needing additional probing.
- **Active shaping:** Very high. Kamen made every meaningful technical call himself — picked LangGraph, picked Opus/Sonnet split, upgraded fundamentals to LLM call, called the fail-hard policy, picked the confidence indicator, picked Strategy C explicitly with reasoning ("less business logic on UI"), endorsed artificial pacing on first hearing it, chose monorepo + early header emit + .md prompts in one decisive answer. He's in the driver's seat — the role here is competent technical sparring partner, not architect.
- **PRD open questions resolved:** Q1 (header metrics curation). Q2 + Q3 deferred to /build as planned.

## /checklist
- **Sequencing decision:** Backend-first, inside-out. Kamen noted his usual instinct is frontend-first with mocks, but explicitly flipped for this project because the learning target (LangGraph + SSE) lives in the backend — strong self-aware sequencing call. Graph skeleton with stubs (step 2) and SSE pacing (step 3) land before any LLM/yfinance work so the new/risky surface is battle-tested early. Endpoints and real agents layer on top (4–7). Frontend consumes a known-good SSE contract (8–9b). Polish + submit closes (10).
- **Tests:** Kamen asked to add pytest coverage on his own initiative — another signal he's taking the backend learning seriously, not just rushing to a demo.
- **Build mode:** Step-by-step. Aligned with learning goal — wants to see the LangGraph wiring unfold rather than review a monolithic autonomous build.
- **Comprehension checks:** Yes for backend/graph items (2–7), off for frontend items. Tailored choice — he recognized frontend is familiar territory and wouldn't benefit from checks, but LangGraph/SSE mechanics should be actively recalled.
- **Verification:** Yes — per-item. Accepted without pushback.
- **Check-in cadence:** Learning-driven. Wants decision narration during build, especially on the new orchestration surface.
- **Git cadence:** Commit per step with `step N: [title]` message format. Accepted immediately.
- **Demo tickers:** AAPL (safe, rich) + FIG/Figma (learner's suggestion — thematic fit with his design sensibility, fresh IPO surfaces implicit-connection material well). Good creative call.
- **Gitignore:** Kamen created the local repo mid-conversation and asked for a proper `.gitignore`. Written to cover Python (venv, pytest/mypy/ruff caches), Next.js (node_modules, `.next`, pnpm), env files with `.env.example` preserved, macOS/IDE noise, and retains his pre-existing `.claude/` rule.
- **Item count + time:** 11 items (one split — 9 → 9a/9b at Kamen's agreement), ~3.5 hours estimated. Backend 1–7 ≈ 2hr, frontend 8–9b ≈ 1hr, polish/submit ≈ 30min.
- **Split rationale (9 → 9a/9b):** Original step 9 bundled SSE consumer + progress + header + cards + error + 5 components in one item — too big for one step-by-step session. Kamen agreed immediately when flagged. 9a focuses on streaming mechanics + header, 9b focuses on the payoff UI (cards + error).
- **Submission planning:** Core story lead is three-perspectives + LangGraph orchestration as learning angle. Wow moment identified as implicit connections. Local-only deployment confirmed; demo video recommended (60-90s, YouTube unlisted). GitHub repo already created locally with remote set — no repo-creation needed in submission item.
- **Confident on:** Sequencing (backend-first flip was his call), methodology choices, git cadence, demo tickers.
- **Needed guidance on:** Granularity of step 9 (accepted split when flagged), Devpost submission planning details.
- **Deepening rounds:** 0 chosen. Pattern from /scope, /prd, /spec holds — Kamen moves decisively through mandatory questions and opts to proceed. Rich mandatory-phase conversation gave the checklist strong material without additional probing.
- **Active shaping:** High. Kamen drove the backend-first flip (against his own default), added pytest coverage on his own initiative, calibrated comprehension checks by domain (backend yes, frontend no), suggested FIG as a second demo ticker tied to his design identity, and agreed to the 9-split quickly when risk was flagged. Decisive, self-aware, owns the plan.

## /build

### Step 1: Project scaffolding (backend + frontend skeletons)
- **What was built:** Backend and frontend scaffolds were already in place from prior work — verified backend `pyproject.toml` has all required deps (fastapi, uvicorn, langgraph, anthropic, yfinance, pydantic, python-dotenv, sse-starlette, pytest, pytest-asyncio), `main.py` stubs `GET /health`, `.env.example` present. Frontend is Next.js 16 + React 19 + Tailwind 4 + App Router via pnpm, with `.env.local.example` set.
- **Issues encountered:** `uv sync` failed with `yfinance>=1.2.2` — pin was wrong (real yfinance versioning is 0.2.x). Kamen fixed the pin himself after I flagged it; rejected my edit attempt.
- **Learner verification:** Confirmed "both the frontend and backend works" after the pin fix.
- **Notable:** `frontend/AGENTS.md` warns this Next.js version has breaking changes — docs live in `node_modules/next/dist/docs/`. Must consult those before writing frontend code in steps 8–9b.

