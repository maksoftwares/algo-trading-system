# H4 Macro Pullback Reclaim v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 30-160
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 30%-75%
Expected worst single month: -6R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Strict macro-regime H4 EMA50 pullback/reclaim trades with wider stops and lower spread sensitivity than intraday retest systems.

## Mechanical Definition

This candidate tests whether the D1 trend-confirmation layer in the macro momentum confluence family is over-filtering useful strict-macro H4 pullback signals. It keeps strict macro evidence but removes D1 trend confirmation.

Data source:

- XAUUSD H4 broker bars from the existing 9-cell matrix.
- Existing public macro frames used by the macro-composite family: real yield, broad dollar, breakevens, Treasury curve, credit spreads, VIX, GVZ, and Chicago Fed financial conditions.
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
   - strict bullish macro regime
   - H4 low trades within `1.10 x ATR14` above EMA50
   - H4 close is no more than `0.10 x ATR14` below EMA50
   - H4 candle closes bullish
   - H4 3-bar return >= -0.08%
   - H4 12-bar return >= -2.00%
   - close location >= 0.52
   - close no more than `3.20 x ATR14` above EMA50
3. Short setup mirrors the long setup.
4. At most one signal per UTC day and direction.
5. Trade plan uses market entry, `1.55 x H4 ATR14` stop, `1.60R` target, and planned 10-H4-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 375 points.
- Measured median spread: 50 points = 0.1333R.
- Measured P95 spread: 75 points = 0.2000R.
- Structural status: PASS.

## Expected Behavior

The candidate expects strict macro state to be the key source of v0's PF edge. If D1 trend confirmation was mostly starving the sample, removing it while keeping strict macro evidence should increase trade count without collapsing into v1's weak-macro failure.

## Why This Hypothesis Should Exist

`h4_macro_momentum_confluence_v0` had 9/9 PF cells but too few trades. v1 weakened macro votes and failed PF. v2 kept strict macro and broadened H4 execution but still missed trade count and PF persistence. This candidate tests a separate broadening dimension: remove D1 confirmation, keep strict macro, and retain H4 pullback/reclaim structure.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
