# H4 Macro Momentum Confluence v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 20-120
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 30%-70%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: H4 macro-regime pullback/reclaim trades with moderate right-tail and fewer cost-sensitive entries than M5 retest systems.

## Mechanical Definition

This candidate tests a new versioned macro mechanism: shifted macro-composite regime plus shifted D1 trend confirmation plus H4 pullback/reclaim execution. It is not a retune of `h4_macro_composite_risk_state_v0` because v0 used same-bar H4 momentum only; this candidate requires D1 trend alignment and an H4 pullback through/near EMA50 before reclaim.

Data source:

- XAUUSD H4 and D1 broker bars from the existing 9-cell matrix.
- Existing public FRED/FRED-like macro frames used by the macro-composite family: real yield, broad dollar, breakevens, Treasury curve, credit spreads, VIX, GVZ, and Chicago Fed financial conditions.
- All daily macro and D1 features are shifted by one completed observation before H4 alignment.

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

D1 confirmation:

1. Compute D1 ATR14, EMA20, and 5-day return.
2. Long requires shifted D1 close above EMA20 and 5-day return >= +0.15%.
3. Short requires shifted D1 close below EMA20 and 5-day return <= -0.15%.

H4 execution:

1. Compute H4 ATR14, EMA50, 3-bar return, and 12-bar return.
2. Long setup:
   - bullish macro regime
   - shifted D1 bullish confirmation
   - H4 low trades within `0.75 x ATR14` above EMA50
   - H4 close reclaims above EMA50
   - H4 candle closes bullish
   - H4 3-bar return >= +0.08%
   - H4 12-bar return >= -1.20%
   - close location >= 0.55
   - close no more than `2.75 x ATR14` above EMA50
3. Short setup mirrors the long setup below EMA50.
4. At most one signal per two-day bucket and direction.
5. Trade plan uses market entry, `1.55 x H4 ATR14` stop, `1.60R` target, and planned 10-H4-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 375 points.
- Measured median spread: 50 points = 0.1333R.
- Measured P95 spread: 75 points = 0.2000R.
- Structural status: PASS.

## Expected Behavior

The candidate expects macro-composite regimes to work better when XAU is already aligned on D1 and the H4 entry occurs after a pullback/reclaim rather than chasing any same-bar macro-aligned momentum. If the mechanism exists, it should preserve the all-positive character of v0 while improving trade count and Capital.com transfer.

## Why This Hypothesis Should Exist

`h4_macro_composite_risk_state_v0` produced a meaningful independent clue: 6/9 PF cells, 6/9 trade-count cells, and 9/9 positive cells, but it was too sparse in Capital.com and failed activity/concentration. `h4_macro_composite_risk_state_v1` broadened participation and diluted the edge. This candidate tests a different broadening path: do not lower macro evidence alone; require D1 trend structure plus H4 pullback/reclaim execution.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
