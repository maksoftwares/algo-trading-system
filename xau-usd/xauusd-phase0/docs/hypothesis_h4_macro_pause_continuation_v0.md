# H4 Macro Pause Continuation v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 40-180
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 30%-70%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: H4 macro-regime continuation trades after short pauses, with moderate right-tail and wider stops than intraday retest systems.

## Mechanical Definition

This candidate tests a new versioned macro mechanism: strict shifted macro-composite regime plus H4 continuation after a short pause. It is independent of the level/retest family because it does not use round levels, swing levels, session extremes, breakout retests, or pending limit retests. It is also not a direct retune of `h4_macro_momentum_confluence_v0` because it removes the shifted D1 trend gate and replaces EMA50 pullback/reclaim with a continuation-after-pause condition.

Data source:

- XAUUSD H4 broker bars from the existing 9-cell matrix.
- XAUUSD D1 broker bars only for inherited feature preparation compatibility; D1 values are not setup gates.
- Existing public FRED/FRED-like macro frames used by the macro-composite family: real yield, broad dollar, breakevens, Treasury curve, credit spreads, VIX, GVZ, and Chicago Fed financial conditions.
- All daily macro features are shifted by one completed observation before H4 alignment.

Macro regime features:

1. Use the existing macro-composite vote construction from `h4_macro_composite_risk_state_v0`.
2. Bullish macro regime requires:
   - `macro_composite_score >= 2`
   - `macro_bull_votes >= 3`
   - `macro_bear_votes <= 1`
3. Bearish macro regime requires:
   - `macro_composite_score <= -2`
   - `macro_bear_votes >= 3`
   - `macro_bull_votes <= 1`

H4 execution:

1. Compute H4 ATR14, EMA50, 3-bar return, and 12-bar return.
2. Long setup:
   - bullish macro regime
   - H4 close above EMA50
   - H4 candle closes bullish
   - H4 12-bar return >= +0.20%
   - H4 3-bar return between -0.40% and +1.00%
   - close location between 0.45 and 0.82
   - close is between `0.05 x ATR14` and `3.60 x ATR14` above EMA50
3. Short setup mirrors the long setup below EMA50.
4. At most one signal per one-day bucket and direction.
5. Trade plan uses market entry, `1.55 x H4 ATR14` stop, `1.55R` target, and planned 10-H4-bar time stop inherited from the macro confluence base.

Measured-cost structural precheck:

- Expected median stop distance: 375 points.
- Measured median spread: 50 points = 0.1333R.
- Measured P95 spread: 75 points = 0.2000R.
- Structural status: PASS.

## Expected Behavior

The candidate expects strict macro-composite regimes to preserve the PF quality seen in `h4_macro_momentum_confluence_v0`, while removing the D1 trend filter and EMA50 retest requirement should improve trade count and reduce zero-trade-month concentration. The short-pause condition is intended to avoid chasing vertical H4 bars while still participating in macro-aligned continuation.

## Why This Hypothesis Should Exist

The current independent search has a useful but incomplete macro clue: `h4_macro_momentum_confluence_v0` reached 9/9 PF cells above 1.30 and all cells profitable, but only 5-30 trades per cell with high zero-month concentration. Later broadening attempts either diluted PF or stayed too sparse. This candidate tests a separate broadening path: keep strict macro evidence, remove D1 confirmation, and require H4 continuation after a pause instead of a pullback/reclaim.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
