# Beauty Score Formulas — Remaining Strategies

Today, the full weighted "beauty score" (0-100 + A-F grade, `BaseBeautyModel` convention: A≥80, B≥70, C≥60, D≥50, F<50 — [base_model.py](../../tradeseeker-batch-v2/src/beauty_models/base_model.py)) only covers **ATH** and **Near-ATH** ([original_model.py](../../tradeseeker-batch-v2/src/beauty_models/original_model.py)). The other four strategies either have no score, or a thin single-signal placeholder that throws away data the detector already computes:

| Strategy | Current scoring | Gap |
| --- | --- | --- |
| ATH / Near-ATH | Full 5-component beauty score (consolidation, volume, momentum, green candle, gap) | — (reference model) |
| Golden Cross / Death Cross | `crossover_strength` = raw `ema_50 - ema_200` in price units | Not normalized across price levels, not a 0-100 score, no volume/momentum/trend-quality factored in at all |
| Speculative | `speculative_score = 25 × count(4 binary flags)` | Coarse — a 3.1x volume spike scores identical to a 10x spike; magnitude is thrown away |
| Divergence | `divergence_score = clamp(0,100,(rsi_2−rsi_1)×5)` | Single signal (RSI gap only) — ignores price-structure quality and recency as separate factors |
| Confirmed Reversal | Same single-signal formula as Divergence | **Doesn't use `bounce_pct` at all**, even though it's already computed in [confirmed_reversal_detector.py](../../tradeseeker-batch-v2/lambdas/downloader/confirmed_reversal_detector.py) and is the entire reason this strategy exists separately from Divergence |

This doc proposes a formula for each gap, grounded in fields each detector already computes (or can cheaply add), following the same design conventions as the existing models: percentage/ratio-based (not absolute price, since markets span THB/HKD/CNY/KRW/TWD/USD), curve-shaped component scores (not hard binary cutoffs), weighted composite to 0-100.

---

## 1. Golden Cross / Death Cross

Reuses the spirit of the existing [ema_model.py](../../tradeseeker-batch-v2/src/beauty_models/ema_model.py) (EMA separation/momentum curves already exist there) but adds two things a generic EMA model doesn't have: **freshness of the specific cross event** and a **whipsaw penalty**, since a golden cross printed three weeks after a death cross in the same stock is a much weaker signal than a clean first cross.

| Component | Weight | Formula |
| --- | --- | --- |
| Crossover Strength | 20% | `sep_pct = (ema_50 − ema_200) / ema_200 × 100` at the cross day. Score: ≥5%→100, ≥3%→80+(sep−3)×10, ≥1%→60+(sep−1)×10, ≥0.5%→40+(sep−0.5)×40, else sep×80 — same curve shape as `ema_model.py`'s separation score |
| Volume Confirmation | 20% | Volume on the cross day ÷ trailing-30d average volume. Score: ratio≥3.0→100, ≥2.0→80+(r−2)×20, ≥1.5→60+(r−1.5)×40, ≥1.0→40+(r−1)×40, else r×40 — identical curve to `original_model.py`'s `_calculate_volume_score` |
| Momentum Continuation | 25% | % price change over each of the next 5 trading days vs. the cross-day close, scored per-day (>5%→25pts, >2%→20pts, >0%→15pts, >−2%→10pts, else 0) and averaged ×4 — identical shape to `original_model.py`'s `_calculate_momentum_score` |
| Trend Quality (whipsaw penalty) | 20% | Count EMA50/200 crosses (either direction) in the trailing 90 days *before* this one. 0 prior→100, 1→70, 2→40, 3+→10 |
| Long-Term Trend Slope | 15% | `ema200_slope_pct = (ema_200_today − ema_200_20d_ago) / ema_200_20d_ago × 100`. ≥1%→100, ≥0%→50+slope×50, <0%→max(0, 50+slope×25) |

```
golden_cross_beauty_score =
    0.20 × crossover_strength_score +
    0.20 × volume_confirmation_score +
    0.25 × momentum_continuation_score +
    0.20 × trend_quality_score +
    0.15 × long_term_slope_score
```

**Death Cross** uses the same five components mirrored for the bearish direction (`sep_pct = (ema_200 − ema_50)/ema_200 × 100`, momentum continuation measured as downside follow-through, slope measured as EMA200 declining). Since death-cross is intentionally hidden from the UI today ([strategy-selector.component.ts:22](../../tradeseeker-web-v2/tradeseeker-web-v2/src/app/features/dashboard/components/strategy-selector/strategy-selector.component.ts#L22)), this is lower priority to implement — wire it once death-cross is ever surfaced.

**New data needed:** `cross_detector.py` currently only returns `ema_50`, `ema_200`, `crossover_strength` at the cross date — it doesn't carry volume or the trailing EMA/cross history needed for components 2, 4, 5. These are all already present in the `price_data`/`moving_averages` arrays passed through the pipeline, so this is wiring, not new data collection.

---

## 2. Speculative — Risk Score, Not a Beauty Score

**This one shouldn't get an A-F beauty grade at all.** Beauty scores mean "how good is this opportunity" — higher is better. Speculative detection means the opposite: "how much caution does this setup deserve" — higher should mean *more* risk, not *more* opportunity. Forcing it into the A-F convention would mean "Grade A speculative stock" reads as a recommendation when it should read as a warning. Keep it a separate **Risk Score** with its own labels (e.g. Low / Moderate / High / Extreme), not graded on the same scale as everything else.

The current formula (`25 × count of 4 binary flags`) is a reasonable skeleton but loses magnitude — upgrade each flag to a continuous 0-25 sub-score instead of a binary 0-or-25:

| Component | Weight (pts) | Formula |
| --- | --- | --- |
| Volume Spike | 0-25 | `volume_spike_ratio` (already computed): <3.0×→0, scales linearly 3.0×–6.0×→0-25, caps at 25 beyond 6.0× |
| Volatility Spike | 0-25 | `recent_volatility_pct` (already computed): <30%→0, scales linearly 30%-60%→0-25, caps at 25 beyond 60% |
| Red Candle Severity | 0-25 | `max_red_candle_30d_pct` (already computed): >−15%→0, scales linearly −15% to −40%→0-25, caps at 25 beyond −40% |
| Run-up Steepness | 0-25 | `cumulative_return_10d_pct` (already computed): <30%→0, scales linearly 30%-80%→0-25, caps at 25 beyond 80% |

```
risk_score = volume_spike_pts + volatility_pts + red_candle_pts + run_up_pts   // 0-100
```

Keep the existing `speculative_score >= 50` gate (now interpretable as "risk score ≥ 50" rather than "≥2 flags"). All four input fields already exist in [speculative_detector.py](../../tradeseeker-batch-v2/lambdas/downloader/speculative_detector.py) — this is a pure formula upgrade, no new data.

---

## 3. Divergence

Currently one signal (RSI gap × 5) decides the whole score. Already-computed facts not currently used in scoring: `price_2`/`price_1` (the two swing-low prices) and `days_since_low`.

| Component | Weight | Formula |
| --- | --- | --- |
| RSI Divergence Strength | 40% | `clamp(0, 100, (rsi_2 − rsi_1) × 6)` — same signal as today, reduced from 100% to 40% weight |
| Price Structure Quality | 25% | `decline_pct = (price_1 − price_2) / price_1 × 100` (how much lower the new low actually undercut the prior one). 0%→20, 2%→60, ≥5%→100 |
| Recency | 20% | `days_since_low` (already computed, gated ≤20 by the detector): 0-5d→100, 6-12d→70, 13-20d→40 |
| RSI Floor Depth | 15% | `rsi_2` itself, inverted (more oversold = stronger setup): ≤30→100, 50→0, linear between |

```
divergence_beauty_score =
    0.40 × rsi_gap_score +
    0.25 × price_structure_score +
    0.20 × recency_score +
    0.15 × rsi_floor_score
```

No new data needed — `price_2`, `price_1`, and `days_since_low` are already returned by [divergence_detector.py](../../tradeseeker-batch-v2/lambdas/downloader/divergence_detector.py)'s `find_lower_low_higher_rsi()`, just not currently fed into the score.

---

## 4. Confirmed Reversal

Same gap as Divergence, plus the more glaring one: `bounce_pct` — the entire reason this strategy exists separately from Divergence (Divergence = "might turn", Confirmed Reversal = "is turning") — is computed in [confirmed_reversal_detector.py:79](../../tradeseeker-batch-v2/lambdas/downloader/confirmed_reversal_detector.py#L79) and then **never used** in the score.

| Component | Weight | Formula |
| --- | --- | --- |
| Bounce Strength | 35% | `bounce_pct` (already computed, gated ≥5%): 5%→40, ≥15%→100 |
| RSI Divergence Strength | 25% | Same as Divergence component 1: `clamp(0, 100, (rsi_2 − rsi_1) × 6)` |
| Recency | 20% | Same `days_since_low` curve as Divergence |
| Volume on the Bounce | 20% | **New field needed**: average volume over the bounce days (from `low_2_date` to today) ÷ trailing-30d average. Same curve as `original_model.py`'s `_calculate_volume_score` — confirms real buying behind the bounce, not a low-volume drift |

```
confirmed_reversal_beauty_score =
    0.35 × bounce_strength_score +
    0.25 × rsi_gap_score +
    0.20 × recency_score +
    0.20 × bounce_volume_score
```

**New data needed:** volume over the bounce window isn't currently captured anywhere in `confirmed_reversal_detector.py` — it has `price_data` available already (passed in), so this is a few lines to slice `price_data` from `low_2_date` to the latest record and average `volume`, not a new data source.

---

## 5. Implementation Notes

- Add new model classes under `tradeseeker-batch-v2/src/beauty_models/` (e.g. `cross_model.py`, `divergence_model.py`, `confirmed_reversal_model.py`) implementing `BaseBeautyModel`, matching the existing `original_model.py` / `ema_model.py` pattern — they already plug into `model_factory.py`'s switching/versioning system, so no new infrastructure is needed, just new model implementations.
- Speculative's Risk Score should **not** go through `BaseBeautyModel._get_beauty_grade()` (the A-F letter grade) — give it its own tier function so a UI never accidentally renders "Grade A" next to a stock flagged as high-risk.
- All four formulas above reuse curve shapes already established elsewhere in the codebase (the piecewise linear ramps from `original_model.py` and `ema_model.py`) rather than inventing new scoring shapes — keeps the scores feeling consistent to a user comparing strategies side by side, and keeps calibration (per `BEAUTY_MODEL_SYSTEM.md`'s `calibrated` model path) viable later, since weights are the tunable surface across all of them.
- Once live, these feed directly into the triage pitch from [scoring-positioning.md](../planning/scoring-positioning.md) — every strategy gets the same "grade first, raw list second" treatment, not just ATH/Near-ATH.
