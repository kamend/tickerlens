# TickerLens

## Idea
A calm, editorially-designed financial research tool where you enter a stock ticker and get three reasoned perspectives — the case for buying, holding, and selling — grounded in real fundamentals and current news, so the investor can make their own informed decision.

## Who It's For
Individual investors like Kamen — people who invest based on intuition and common sense in companies they believe in (Apple, Google, Tesla), but want more substance behind their decisions without drowning in data or paying for premium platforms. Not day traders. Not quants. People who want to understand a company's position clearly before deciding what to do.

## Inspiration & References
- **[Incite AI](https://www.inciteai.com/)** — Right idea (integrates fundamentals, macro, news), but the interface is overcrowded and poorly arranged. TickerLens takes the same depth of reasoning but presents it with clarity and hierarchy.
- **[VectorVest](https://www.stockbrokers.com/guides/ai-stock-trading-bots)** — Interesting for its clear Buy/Sell/Hold signal. TickerLens borrows the three-verdict structure but shows the reasoning behind each, rather than collapsing it into a single score.
- **[WarrenAI](https://www.investing.com/warrenai)** — Conversational and accessible, but too generic. No opinion, no edge. TickerLens is opinionated — it presents real arguments, not just data.
- **Design energy:** Light, calm, inviting. Serif font. Editorial feel — like reading a well-written analyst note, not staring at a trading terminal. Deliberately NOT dark mode. Not overly colorful. Purposeful and clean, with the craft sensibility of tools like Raycast and Glaze.

## Goals
- Build a tool with real user value — something Kamen would actually reach for when evaluating a stock.
- Practice agent orchestration: multiple agents with distinct responsibilities (fundamentals, news/macro, synthesis) coordinating to produce a unified output.
- Create something visually polished that reflects strong design taste — proof that AI-built tools don't have to look generic.

## What "Done" Looks Like
A web app with a single input field. You type a ticker (e.g., AAPL). You get back:
1. **Header section** — Company name, ticker, price, and a handful of key fundamentals (P/E, market cap, etc.). Essential context, not a data dump.
2. **Three cards: Buy / Hold / Sell** — Each presents a concise, reasoned argument for that action, grounded in real fundamental data and current news/macro context. This includes implicit connections — not just "Apple reported earnings" but "new EU digital payments regulation could impact Apple's services revenue."
3. **Expandable detail** — Each card can be expanded for deeper reasoning and sources.

The whole experience feels calm, editorial, and trustworthy. The user reads three perspectives and makes their own call.

## What's Explicitly Cut
- **Portfolio tracking / multi-stock analysis** — No adding your holdings, no portfolio risk assessment. One ticker at a time.
- **Historical charts or technical analysis** — No candlesticks, no moving averages. This is fundamentals + news, not charting.
- **User accounts or saved searches** — No persistence. Enter a ticker, get an answer.
- **Real-time trading signals or alerts** — This is research, not trading automation.
- **Chat interface** — Despite early brainstorming, the final direction is a direct input/output flow, not a conversational chatbot.

## Loose Implementation Notes
- **Frontend:** Next.js with a clean, minimal UI. Serif typography. Light palette.
- **Data:** Yahoo Finance API (via Python library) for fundamentals. Web search or news API for recent news and macro context.
- **Agent orchestration:** Multiple agents coordinating — one for company fundamentals, one for news/macro scanning, one for synthesis and argument generation. Orchestrated via Claude API / Anthropic SDK.
- **LLM reasoning:** The core value is in the synthesis — connecting data points, identifying implicit news connections, and constructing coherent arguments for each of the three positions.
