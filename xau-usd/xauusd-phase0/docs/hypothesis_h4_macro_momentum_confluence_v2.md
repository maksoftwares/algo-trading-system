# H4 Macro Momentum Confluence v2 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v2
Author / owner: maksoftwares / Codex
Expected trade count per year: 25-140
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 30%-75%
Expected worst single month: -6R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Strict macro-regime H4 pullback/reclaim trades with more participation than v0 but stronger macro evidence than v1.

## Mechanical Definition

This candidate is a fresh versioned broadening of `h4_macro_momentum_confluence_v0`. It keeps v0's strict macro-composite vote requirement because v1 showed that weaker macro votes destroy PF. It broadens only the H4 execution shape and signal throttle.

Data source:

- XAUUSD H4 and D1 broker bars from the existing 9-cell matrix.
- Existing public macro frames used by the macro-composite family: real yield, broad dollar, breakevens, Treasury curve, credit spreads, VIX, GVZ, and Chicago Fed financial conditions.
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
2. Long requires shifted D1 close above EMA20 and 5-day return >= 0.
3. Short requires shifted D1 close below EMA20 and 5-day return <= 0.

H4 execution:

1. Compute H4 ATR14, EMA50, 3-bar return, and 12-bar return.
2. Long setup:
   - strict bullish macro regime
   - shifted D1 bullish confirmation
   - H4 low trades within `1.35 x ATR14` above EMA50
   - H4 close is no more than `0.25 x ATR14` below EMA50
   - H4 candle closes bullish
   - H4 3-bar return >= -0.05%
   - H4 12-bar return >= -1.80%
   - close location >= 0.50
   - close no more than `3.50 x ATR14` above EMA50
3. Short setup mirrors the long setup.
4. At most one signal per UTC day and direction.
5. Trade plan uses market entry, `1.55 x H4 ATR14` stop, `1.60R` target, and planned 10-H4-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 375 points.
- Measured median spread: 50 points = 0.1333R.
- Measured P95 spread: 75 points = 0.2000R.
- Structural status: PASS.

## Expected Behavior

The candidate expects v0's PF edge to survive a broadening that respects the same strict macro regime. If the sparse edge came from the macro state rather than a narrow candle shape, v2 should increase activity without collapsing into the v1 failure pattern.

## Why This Hypothesis Should Exist

`h4_macro_momentum_confluence_v0` passed PF in 9/9 cells but failed activity with only 5-30 trades per cell. `h4_macro_momentum_confluence_v1` solved trade count but failed PF after weakening macro votes. This v2 tests a third path: keep the macro state strict and broaden the H4 entry mechanics.

## What Would Falsify It

Reject v2 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v2 thresholds after first-pass results.
