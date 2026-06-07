# H4 Macro Momentum Confluence v1 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v1
Author / owner: maksoftwares / Codex
Expected trade count per year: 30-160
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 30%-75%
Expected worst single month: -6R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Broader H4 macro-regime pullback/reclaim trades with lower sparsity than v0 and acceptable dilution only if cross-broker PF persists.

## Mechanical Definition

This candidate is a fresh versioned broadening of `h4_macro_momentum_confluence_v0`. It keeps the same independent mechanism: shifted macro-composite regime, shifted D1 trend confirmation, and H4 pullback/reclaim execution. It broadens by allowing a weaker but still directional macro vote state and a less exact EMA50 reclaim.

Data source:

- XAUUSD H4 and D1 broker bars from the existing 9-cell matrix.
- Existing public macro frames used by the macro-composite family: real yield, broad dollar, breakevens, Treasury curve, credit spreads, VIX, GVZ, and Chicago Fed financial conditions.
- All daily macro and D1 features are shifted by one completed observation before H4 alignment.

Macro regime features:

1. Use the existing macro-composite vote construction from `h4_macro_composite_risk_state_v0`.
2. Bullish macro regime requires:
   - `macro_composite_score >= 1`
   - `macro_bull_votes >= 2`
   - `macro_bear_votes <= 1`
3. Bearish macro regime requires:
   - `macro_composite_score <= -1`
   - `macro_bear_votes >= 2`
   - `macro_bull_votes <= 1`

D1 confirmation:

1. Compute D1 ATR14, EMA20, and 5-day return.
2. Long requires shifted D1 close above EMA20 and 5-day return >= 0.
3. Short requires shifted D1 close below EMA20 and 5-day return <= 0.

H4 execution:

1. Compute H4 ATR14, EMA50, 3-bar return, and 12-bar return.
2. Long setup:
   - bullish macro regime
   - shifted D1 bullish confirmation
   - H4 low trades within `1.20 x ATR14` above EMA50
   - H4 close is no more than `0.15 x ATR14` below EMA50
   - H4 candle closes bullish
   - H4 3-bar return >= 0
   - H4 12-bar return >= -1.80%
   - close location >= 0.52
   - close no more than `3.25 x ATR14` above EMA50
3. Short setup mirrors the long setup.
4. At most one signal per two-day bucket and direction.
5. Trade plan uses market entry, `1.55 x H4 ATR14` stop, `1.60R` target, and planned 10-H4-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 375 points.
- Measured median spread: 50 points = 0.1333R.
- Measured P95 spread: 75 points = 0.2000R.
- Structural status: PASS.

## Expected Behavior

The candidate expects v0's cross-broker PF clue to survive a modest activity broadening because the broadening is anchored by D1 trend and H4 pullback/reclaim structure rather than by macro votes alone.

## Why This Hypothesis Should Exist

`h4_macro_momentum_confluence_v0` passed PF in 9/9 cells but failed trade count with only 5-30 trades per cell. `h4_macro_composite_risk_state_v1` showed that broadening macro votes alone diluted the edge. This v1 asks whether the v0 confluence mechanism can broaden activity while preserving cross-broker PF.

## What Would Falsify It

Reject v1 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v1 thresholds after first-pass results.
