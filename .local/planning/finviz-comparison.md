# EveryATH vs. Finviz Screener

Head-to-head between the current EveryATH product (as built in this repo) and Finviz's screener page — the default "free screener" most traders already use, and the hardest incumbent habit to break (see [competitors.md](competitors.md) section 2).

## 1. How Finviz's Screener Actually Works

- Filters are organized into tabs: **Descriptive, Fundamental, Technical, News, ETF** (plus an "All" view), with 60+ pre-built filters — market cap, P/E, float, sector, RSI, SMA crosses, analyst ratings, insider activity, etc.
- A **Signal** menu offers pre-built one-click screens for common events: *New High* (52-week high today), *Top Gainers*, *Unusual Volume*, etc. — closest thing Finviz has to a "strategy."
- Elite tier ($39.50/mo) adds: real-time data, email alerts, a **Custom tab** to choose/reorder displayed columns, and the ability to **save, rename, and share** screens.
- Output is a **table of tickers** matching the filter — no narrative, no ranking by setup quality, no explanation. To judge a result you click into Finviz's own stock page (or elsewhere) for the chart.
- Coverage is overwhelmingly **US-listed equities** (NYSE/NASDAQ/AMEX) plus ETFs/forex/futures screens as separate tools.

## 2. What EveryATH Actually Has Today (from this codebase)

Per the API routes in [router.py](../../tradeseeker-api-v2/src/router.py):

| Endpoint | What it is |
| --- | --- |
| `GET /ath` | Stocks that just hit a new all-time high |
| `GET /near-ath` | Stocks within a configurable % of ATH, not yet breaking it (see [NEAR_ATH_FEATURE.md](../../NEAR_ATH_FEATURE.md)) |
| `GET /golden-crosses` / `GET /death-crosses` | 50/200-day MA crossover signals |
| `GET /speculative` | Speculative-setup strategy |
| `GET /divergence` | Divergence strategy |
| `GET /confirmed-reversal` | Confirmed-reversal strategy |
| `POST /explain-chart` | Sends the stock's chart image **+ real computed numbers** (price, % change over 1/3/12mo, 52-week range, EMA position, volume vs. average) to a vision model, returns one specific, data-grounded paragraph — not generic boilerplate (see [explain_chart.py](../../tradeseeker-api-v2/src/handlers/explain_chart.py)) |
| `GET /openai-summary` | AI-generated stock summary |
| `GET /watchlist`, `/positions` | Saved stocks, with a `held` flag to track open positions |

Each strategy result is ranked by a **beauty score** (breakout quality, with volatility filtering to reject noisy setups), not just a raw filter match. Market coverage already spans US plus several Asian markets and commodities (git history shows HK, China, Korea, Taiwan, Thailand, plus Gold/Oil) — broader than Finviz's US-centric default.

## 3. Side-by-Side

| Dimension | Finviz Screener | EveryATH |
| --- | --- | --- |
| **Core model** | User builds a filter (or picks a Signal preset) across 60+ fields | Pre-built strategies (ATH, Near-ATH, Golden/Death Cross, Divergence, Reversal) — no filter-building required |
| **Output** | Flat table of matching tickers | Ranked list by beauty score, per strategy |
| **Explanation** | None — table of numbers only | Per-stock AI paragraph grounded in real computed numbers (not a generic vision-model guess) |
| **Setup effort** | Medium-high — need to know what filters to combine to express a strategy | Zero — strategy is already the product |
| **Breadth of filters** | Very high (60+ fields, fundamentals + technicals + descriptive) | Narrow by design — a handful of named strategies, not a general filter builder |
| **Markets** | Primarily US-listed equities | US + multiple Asian markets + commodities |
| **Alerts** | Email alerts (Elite tier only) | Not yet shipped (see [sns.md](sns.md) — currently a pull/visit product, not push) |
| **Save/share screens** | Yes (Elite) | N/A — strategies are fixed, not user-defined |
| **Position tracking** | No | Yes — watchlist + held-position flag |
| **Price** | Free tier limited; Elite ~$39.50/mo | TBD |
| **Brand maturity** | Long-established, default "free screener" in FinTwit | New, no brand recognition yet |

## 4. Where Finviz Wins

- **Filter breadth and flexibility** — a power user can express almost any screen Finviz's 60+ fields allow; EveryATH's fixed strategy list can't replicate arbitrary custom filters.
- **Brand trust and habit** — it's the default free tool traders already have open in a tab. Any new product has to earn a reason to be a *second* tab, not replace the first.
- **Custom columns / save & share** — lets power users build a personal workflow and share it with others, which also drives Finviz's own organic growth (shared screens circulate on FinTwit).
- **Fundamentals depth** — P/E, insider transactions, analyst ratings, etc. EveryATH is technical-signal-only today.

## 5. Where EveryATH Wins (or Can)

- **Zero setup, immediate value** — a trader doesn't need to know which filter combination expresses "golden cross" or "near-ATH breakout"; it's already a named result set. Finviz requires knowing the Signal menu exists or building the filter yourself.
- **Explanation attached to the result** — Finviz's output is pure data; EveryATH's `/explain-chart` ties plain language directly to real computed numbers per stock. This is the gap identified in [competitors.md](competitors.md) section 5 — only Breakout Scanner and ChartingLens are moving this direction among the broader competitor set, and Finviz isn't one of them at all.
- **Ranking by setup quality** (beauty score), not just a binary filter match — helps a trader triage a list instead of scanning every row manually.
- **Broader market coverage** (Asian markets + commodities) that Finviz's free/Elite tiers don't emphasize.
- **Position tracking built in** (watchlist + held flag) — Finviz screener doesn't track what you actually hold.

## 6. Gaps to Close Before This Comparison Is a Fair Fight

- **No push alerts yet** — Finviz Elite already emails you on a match; until EveryATH ships alerts, a trader still has to remember to visit the site (this is exactly the gap [sns.md](sns.md) is trying to solve via X/distribution in the meantime).
- **No custom filter builder** — fine as a deliberate narrow-wedge choice (per [positioning.md](positioning.md)), but means EveryATH can never be a Finviz *replacement* for power users who want arbitrary screens — only a complement for the specific strategies it covers.
- **No saved/shareable screens** — nothing to go viral the way a shared Finviz preset does on FinTwit.
- **Unproven brand/track record** — Finviz's biggest asset is really just incumbency; EveryATH's weekly Track Record recap (from [sns.md](sns.md)) is the intended counter to this over time.

## Bottom Line

Finviz is a general-purpose filter engine with huge breadth and zero explanation. EveryATH is the opposite: narrow, pre-built strategies with ranking and plain-English explanation baked in, but no general filter-building and no alerts yet. The pitch to a Finviz user isn't "replace your screener" — it's "stop re-building the same golden-cross/ATH filter every day and stop guessing why a result matters."
