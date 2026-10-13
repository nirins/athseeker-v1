# Positioning EveryATH Around Scoring

The problem with Finviz and Tradmap isn't that they can't find golden crosses or ATH breakouts — they can, for the whole market, for free (see [finviz-comparison.md](finviz-comparison.md), [tradmap-comparison.md](tradmap-comparison.md)). The problem is **what they hand back**: a sortable table of every match, with no answer to "which of these are actually worth my time today." A golden-cross screen can return 50-150+ rows across the US market on a given day — Tradmap's own screen showed 107 matches at last check. A swing trader isn't a day trader glued to a terminal; they check in a few times a day/week and need a shortlist, not a spreadsheet.

**The positioning: Finviz and Tradmap find candidates. EveryATH finds the ones worth looking at.**

## 1. The Asset We Already Have

This isn't a hypothetical feature — it's already built. The **beauty score** (`tradeseeker-batch-v2/src/beauty_models/`) turns every breakout/setup into a single 0-100 score and a letter grade (A-F), computed from five weighted signals:

| Component | Weight | What it measures |
| --- | --- | --- |
| Consolidation | 25% | How tightly the price was consolidated before the breakout (low volatility = real base, not noise) |
| Momentum | 25% | Whether price actually continued higher in the days after the signal |
| Volume | 20% | Size of the volume surge on the breakout day vs. recent average |
| Green candle | 20% | % of up-candles in the days around the breakout |
| Gap | 10% | Whether the breakout gapped up, and by how much |

Two things make this more than "just another indicator":

1. **It's a fusion, not a filter.** Finviz and Tradmap let you *sort* by one column at a time (volume, % change, technical rating). A trader still has to mentally combine five signals themselves, row by row. The beauty score does that fusion once, automatically, for every result.
2. **It's trainable, not just a formula.** The model system (`BEAUTY_MODEL_SYSTEM.md`) supports a fixed-weight baseline (`original`) and a `calibrated` model whose weights are learned from real labeled outcomes — a trader grades charts through the app (the `held` flag + training-data endpoints), and the calibration step re-optimizes the weights against what actually worked. The score gets better the more it's used, instead of being a static heuristic someone guessed once.

## 2. Why Scoring Is the Actual Answer to "Too Many Results"

Competitor research so far is consistent: every one of them — Finviz, Tradmap, Chartink, ChartMill, StockMonitor, MomentumSift — stops at the raw list (see [competitors.md](competitors.md) section 5). None of them compress a long list into "here are the 5 worth checking" for a human with limited time. That compression step is the actual product, not the screening step.

| What a swing trader has to do today | With Finviz/Tradmap | With EveryATH |
| --- | --- | --- |
| Run the golden-cross / near-ATH screen | 1 click | Already done — it's the default view |
| Review results | Open 20-100+ rows, check volume/trend/consolidation manually for each | Sort by grade, open the A/B-graded handful |
| Decide what's worth a closer look | Entirely manual, same effort every single row | Score has already triaged it |
| Understand *why* a result is strong | Not provided at all | Score components + `/explain-chart` narrative, per result |

## 3. Positioning Statement

> **Finviz and Tradmap give you a list. EveryATH gives you a shortlist.**

Supporting lines to test:
- "Stop reading rows. Start reading grades."
- "A golden cross tells you what happened. A grade tells you if it's worth acting on."
- "107 stocks matched the screen. 6 were actually worth your time."

This also folds cleanly into the existing brand/tagline ("Every ATH. Every Opportunity.") — the opportunity isn't "every stock that technically matches a filter," it's "every stock worth your limited attention."

## 4. Product Implications

- **Grade should be the primary sort/default view**, not one more column buried among P/E and sector. Default to showing A/B-grade results first (or only), with the option to expand to the full list — inverting the Finviz/Tradmap model where the full list *is* the product.
- **Pair the score with the explanation.** The beauty score answers "how strong, quantitatively" (consolidation/volume/momentum/etc.); `/explain-chart` answers "why, in plain English." Shown together per result, a trader can approve/reject a setup in seconds without opening a chart elsewhere — this is the one-two punch no competitor researched so far has either half of, let alone both.
- **Show the component breakdown, not just the final number.** A grade with no reasoning feels like a black box (and invites "why should I trust this score" pushback). Surfacing "consolidation 82, volume 95, momentum 60..." lets a trader sanity-check the grade against their own read of the chart — and doubles as the first few sentences of the "how strong is the setup" explanation from [positioning.md](positioning.md) section 4.
- **Use the funnel in marketing.** "X stocks matched the screen today → Y were graded A or B" is a concrete, repeatable, screenshot-able number for the Daily ATH Alerts / Track Record pillars in [sns.md](sns.md) — it's a visceral way to show the triage value without explaining the model.

## 5. The Honest Caveat

The `original` fixed-weight model is a reasonable baseline on its own (it's a sound set of breakout heuristics), but the real pitch — "this score gets smarter from real outcomes" — depends on the `calibrated` model actually having enough labeled training data to be trustworthy. Until there's a meaningful amount of graded history, lead marketing claims with "a single quality grade instead of 5 metrics to eyeball yourself," not "an AI that learns" — the second claim needs the calibration to actually be live and validated first, or it's an overclaim competitors (or users) can poke a hole in.
