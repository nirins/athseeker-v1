# EveryATH vs. Tradmap

Your instinct is right — of everything researched so far ([competitors.md](competitors.md), [finviz-comparison.md](finviz-comparison.md)), **Tradmap is the closest structural match** to what's being built. Finviz makes you build a filter yourself; Tradmap, like EveryATH, ships *named, pre-built strategy screens* you just open. That's the same core product model.

## 1. What Tradmap Is

[tradmap.com](https://tradmap.com/) is a free stock screener/market-intelligence site covering ~5,400 US-listed stocks, sourced from SEC EDGAR fundamentals + end-of-day pricing.

- **55+ filters**, but more importantly **66 ready-made screens** organized by category — this is the part that overlaps with us:
  - *Technical signals*: **Golden Cross** (50/200 MA), Death Cross, uptrend/downtrend, MACD bullish/bearish crossover, RSI oversold bounce / overbought reversal, **new 52-week highs/lows**, **stocks near 52-week highs**, **breakout candidates**, strongly bullish/bearish rating
  - *Valuation & income*: lowest P/E, value/undervalued/overvalued, highest dividend yield
  - *Quality*: highest ROE/ROIC, fastest-growing
  - *Thematic*: AI/chips/cloud/software/power, penny stocks, blue-chips, dividend-by-sector
- Also ships a **daily heatmap**, sector breadth, top movers/gainers/losers, and an earnings/dividend calendar — a broader "market intelligence" surface, not just screens.
- Results are **sortable tables** (symbol, sector, market cap, P/E, price, % change, technical rating, volume), with multiple view modes (overview/valuation/financial/performance/technical/charts/detail/map) and CSV export.
- **No AI-generated explanation**, **no visible alert or watchlist/position-tracking feature**, free with optional login.

## 2. Side-by-Side

| Dimension | Tradmap | EveryATH |
| --- | --- | --- |
| **Core model** | Pre-built named screens (66 of them) — no filter-building required | Pre-built named strategies — same model |
| **Golden Cross** | Yes, dedicated screen | Yes (`/golden-crosses`, `/death-crosses`) |
| **ATH / near-high** | "New 52-week highs" + "stocks near 52-week highs" + "breakout candidates" | `/ath` + `/near-ath` (configurable % threshold, volatility-filtered, beauty-score ranked) |
| **Reversal/momentum** | RSI oversold bounce, overbought reversal, MACD crossovers | `/divergence`, `/confirmed-reversal`, `/speculative` |
| **Ranking of results** | Sortable columns only (no composite quality score) | Beauty score — ranks setup quality, filters out excessive volatility |
| **Per-result explanation** | None — raw table | `/explain-chart`: AI paragraph grounded in real computed numbers (price, % change, 52-week range, EMA position, volume vs. avg) per stock |
| **Breadth beyond technicals** | Much broader — valuation, quality, thematic (AI/semis/etc.), heatmap, earnings calendar | Narrow by design — technical/momentum strategies only |
| **Markets** | ~5,400 US stocks only | US + Asian markets (HK, China, Korea, Taiwan, Thailand) + commodities (Gold, Oil) |
| **Alerts** | Not visible on the site | Not shipped yet either (see [sns.md](sns.md)) |
| **Watchlist / positions** | Not visible | Yes — watchlist + `held` flag |
| **Pricing** | Free | TBD |
| **Brand/traffic** | Unknown scale, but it's a live, indexed, free product already ranking for "golden cross" searches | New, no SEO/brand presence yet |

## 3. Where Tradmap Wins

- **Far more pre-built screens (66 vs. 7)** — valuation, quality, thematic, and income screens that EveryATH doesn't attempt and isn't trying to.
- **Market-intelligence extras**: heatmap, sector breadth, top movers, earnings/dividend calendar — gives a reason to visit daily beyond any single strategy.
- **Already live and free**, with pages apparently already indexed for exactly the terms we'd want to rank for (it showed up directly in a "golden cross screener US stocks" search).
- **Fundamentals depth** (SEC EDGAR-sourced) that EveryATH's technical-signal focus doesn't cover at all.

## 4. Where EveryATH Wins (or Can)

- **Beauty-score ranking** — Tradmap's "breakout candidates" and "near 52-week highs" screens are still just sortable raw tables; nothing composite-scores or quality-filters the list the way the beauty score + volatility rejection does.
- **Per-stock AI explanation grounded in real numbers** — this is the one feature gap that shows up against *every* competitor researched so far (Finviz, Tradmap, Chartink, ChartMill, StockMonitor, etc.). None of them do this.
- **Position tracking** (watchlist + held flag) — Tradmap is screen-only, nothing to track what you actually hold.
- **Non-US market coverage** — if the Asian-market/commodity angle matters to the target audience, Tradmap doesn't compete there at all.

## 5. The Uncomfortable Part

Unlike Finviz (a filter-builder most traders already tolerate the friction of), Tradmap already does almost exactly what EveryATH's Phase 1+2 roadmap describes — named strategy screens including Golden Cross and ATH/near-high/breakout — for free, live, today. If someone searches "golden cross screener" or "near 52-week high screener," Tradmap is already a result (see the earlier research — it was literally one of the pages that surfaced). That means the "pre-built strategy screen" idea by itself is **not defensible** — Tradmap proves it's buildable and already built.

The only parts of the roadmap Tradmap doesn't have are exactly the parts flagged as the real differentiation in [positioning.md](positioning.md) section 4 and [competitors.md](competitors.md) section 5: the **explanation layer** (why it matters, how strong, what to watch) and **ranking by setup quality**, not just a sortable list. If EveryATH ships the same screens as Tradmap but without shipping the explanation/ranking layer convincingly, there's no real reason for a trader to switch.

## Bottom Line

Tradmap validates the "pre-built strategy screens, not a filter builder" model — but also proves that model alone has no moat, because it's already free and live. The explain-chart AI layer and beauty-score ranking are the entire case for EveryATH existing next to Tradmap; without them, EveryATH is just a smaller, narrower, newer version of a tool that already exists.
