# TickerLens — Product Requirements

## Problem Statement
Individual investors who pick stocks based on intuition and belief in companies lack a quick, clear way to pressure-test their thinking. Premium platforms are overwhelming, free tools are shallow, and none present balanced reasoning across multiple perspectives. These investors need a calm, opinionated research tool that lays out the case for buying, holding, and selling — grounded in real data — so they can make their own informed call in minutes, not hours.

## User Stories

### Ticker Input

- As an individual investor, I want to enter a stock ticker and immediately kick off research so that I can get insights on any company I'm curious about without navigating menus or setting up anything.
  - [ ] A centered input field is visible on the landing screen
  - [ ] Typing a ticker and pressing enter/submit begins the validation process
  - [ ] A small inline loader appears (replacing the submit button area) while the ticker is validated
  - [ ] If the ticker is invalid, a soft error message appears below the input field and the user stays on the landing screen
  - [ ] If the ticker is valid, the view transitions smoothly to the results screen

- As an investor who made a typo, I want clear feedback that my ticker wasn't recognized so that I can correct it without confusion.
  - [ ] The error message is friendly and non-technical (e.g., "We couldn't find that ticker. Double-check the symbol and try again.")
  - [ ] The input field retains the entered text so the user can edit rather than retype
  - [ ] The error disappears when the user starts typing again

### Research Progress

- As an investor waiting for results, I want to see what the agents are working on so that I trust real research is happening and stay engaged during the wait.
  - [ ] The results screen shows the company name and ticker anchored at the top, confirming the input was understood
  - [ ] A progress area below shows user-friendly status messages describing what agents are doing (e.g., "Reading Apple's latest earnings...", "Scanning recent regulatory news...", "Building the case for each perspective...")
  - [ ] Messages update as each agent progresses through its work
  - [ ] The transition from input screen to results screen is smooth and animated — no hard cuts

- As an investor whose research failed, I want to understand what went wrong and easily try again so that a backend error doesn't leave me stranded.
  - [ ] If agents encounter an error, an error message replaces the progress area
  - [ ] A back button is visible, allowing the user to return to the input screen
  - [ ] The transition back to the input screen is smooth

### Research Results

- As an individual investor, I want to see essential company context at a glance so that I'm oriented before reading the analysis.
  - [ ] A header section displays company name, ticker, current price, and a small set of key fundamental metrics
  - [ ] The fundamentals shown are curated for relevance — enough to orient, not enough to overwhelm
  - [ ] The header feels like editorial context, not a data dashboard

- As an individual investor, I want to read three distinct perspectives — Buy, Hold, and Sell — so that I can weigh the arguments and make my own decision.
  - [ ] Three cards are displayed: Buy, Hold, and Sell
  - [ ] Each card shows a few sentences summarizing the core argument for that position in its collapsed state
  - [ ] The arguments are grounded in real fundamental data and current news/macro context
  - [ ] Arguments surface implicit connections (e.g., "new EU regulation could impact Apple's services revenue") rather than just restating headlines

- As an investor who wants to dig deeper, I want to expand a card and see the full reasoning with sources so that I can evaluate the evidence myself.
  - [ ] Each card has a clear affordance to expand (click/tap)
  - [ ] Expanding reveals a longer argument with more detail
  - [ ] Referenced articles and sources are included with links
  - [ ] The expand/collapse interaction is smooth and animated
  - [ ] Source presentation format (inline citations vs. reference list) is an open design decision — to be determined during build once real data is available

### Visual Design & Transitions

- As a user, I want the entire experience to feel calm, editorial, and polished so that I trust the tool and enjoy using it.
  - [ ] Light color palette — deliberately not dark mode
  - [ ] Serif typography for an editorial, analyst-note feel
  - [ ] Transitions between states (input → progress → results, results → input) are smooth fades/animations, never jarring cuts
  - [ ] The overall aesthetic is purposeful and crafted — inspired by tools like Raycast and Glaze, not generic financial app templates
  - [ ] Layout has clear visual hierarchy — the eye moves naturally from header to cards

## What We're Building
Everything below must be complete at the end of 3-4 hours:

1. **Landing screen** — Centered ticker input field. Clean, minimal, inviting. Submit triggers validation with inline loading state. Invalid tickers produce a soft, friendly error below the input.

2. **Results screen with agent progress** — Smooth transition from input. Company name and ticker anchored at top. User-friendly progress messages showing what agents are doing in real-time. Error state with back button if agents fail.

3. **Company header** — Company name, ticker, current price, and a curated set of key fundamentals displayed as editorial context.

4. **Three perspective cards (Buy / Hold / Sell)** — Each with a collapsed summary (a few sentences) and expandable detail section with full reasoning and source links. Smooth expand/collapse animation.

5. **Agent orchestration** — Multiple agents coordinating: one for company fundamentals, one for news/macro scanning, one for synthesis and argument generation. Progress streamed to the UI.

6. **Visual polish** — Light palette, serif typography, smooth transitions throughout, editorial feel. No generic AI aesthetic.

## What We'd Add With More Time

- **Recent tickers cache** — Show the last 5 researched tickers on the landing screen. Tap to load cached results if same-day, re-research if stale. Adds persistence and timestamp logic.
- **Search from results page** — Input field or search icon on the results page so you can check another ticker without going back to landing.
- **Source presentation experimentation** — Try inline citations vs. reference lists vs. hybrid approaches once real data reveals what reads best.
- **Richer fundamentals display** — Interactive or contextual fundamentals (e.g., show how a metric compares to industry average on hover).
- **Loading state polish** — More granular agent progress, estimated time remaining, or subtle animations during the wait.

## Non-Goals

1. **No portfolio tracking or multi-stock analysis.** One ticker at a time. No holdings, no risk assessment across positions.
2. **No historical charts or technical analysis.** No candlesticks, no moving averages. This is fundamentals + news, not charting.
3. **No user accounts or saved data.** No login, no persistence, no profiles. Enter a ticker, get an answer.
4. **No real-time trading signals or alerts.** This is a research tool, not trading automation.
5. **No chat interface.** Direct input/output flow. Type a ticker, read the analysis.

## Open Questions

1. **Which specific fundamental metrics to display in the header?** Needs research during /spec — must be curated for an individual investor audience, not a quant. *(Needs answering before /spec.)*
2. **Source link presentation format — inline citations or reference list?** Best determined during build once real source data is available. *(Can wait until build.)*
3. **How to handle tickers with very limited data?** Small-cap or newly listed companies may not have enough fundamentals or news coverage for three strong arguments. Do we show partial results or explain the limitation? *(Can wait until build.)*
