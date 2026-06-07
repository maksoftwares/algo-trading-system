# H1 Volatility Expansion Pullback Continuation v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex

Expected trade count per year: 80-500
Expected cost-adjusted PF: 0.95-1.45
Expected losing-month percentage: 35%-75%
Expected worst single month: -8R to -25R
Expected max consecutive zero months: 3
Expected R-multiple distribution: moderate-frequency H1 continuation losses near -1R with 1.50R wins after high-volatility pullbacks.

## Mechanical Definition

Expert: `h1_volatility_expansion_pullback_continuation_v0`

This is a disabled Phase 0R research candidate. It tests whether XAUUSD trend continuation works better after volatility has already expanded, then price pulls back into a short counter-move and resumes in the original direction.

Data source:

- XAUUSD H1 and M5 bars from the existing broker matrix windows.
- No external, future, or live MT5 data is used.

Feature construction:

1. Calculate H1 ATR(14), EMA(21), EMA(50), 24-hour move in ATR units, 3-hour pullback move in ATR units, ATR(14) 240-bar percentile shifted by one bar, signal candle range/body/close-location, and 6-bar pullback high/low.
2. Volatility expansion is active only when shifted ATR(14) percentile is at least 0.70.
3. Long setup:
   - 24-hour move is at least +2.10 ATR.
   - 3-hour pullback is between -1.25 ATR and -0.25 ATR.
   - Close is above EMA(21), and EMA(21) is above EMA(50).
   - Completed H1 candle is bullish and closes in the upper 38% of its range.
   - Signal candle range is between 0.35 and 2.80 ATR and body ratio is at least 0.30.
4. Short setup:
   - 24-hour move is at most -2.10 ATR.
   - 3-hour pullback is between +0.25 ATR and +1.25 ATR.
   - Close is below EMA(21), and EMA(21) is below EMA(50).
   - Completed H1 candle is bearish and closes in the lower 38% of its range.
   - Signal candle range is between 0.35 and 2.80 ATR and body ratio is at least 0.30.
5. Use at most one signal per UTC day per direction.
6. Entry is next simulated market entry after the completed H1 signal bar.
7. Stop is 0.25 ATR beyond the 6-bar pullback low/high.
8. Target is 1.50R.
9. Planned time stop is 18 completed H1 bars.

Implementation mapping:

- Strategy: `src/phase0/strategies/h1_volatility_expansion_pullback_continuation_v0.py`
- Synthetic fixture: `src/phase0/synthetic.py::_h1_volatility_expansion_pullback_continuation_context`
- Test: `tests/test_h1_volatility_expansion_pullback_continuation_v0.py`

## Expected Behavior

This candidate should produce enough trades to avoid the low-frequency failure mode of many H4/D1 macro lanes, but fewer than naive M15 impulse systems. It should pass only if high-volatility continuation after a controlled pullback is robust across all broker windows and remains viable under p95 costs.

## Why This Hypothesis Should Exist

The previous H1 volatility squeeze breakout lane tested expansion from compression and failed. The smooth-trend exhaustion reversal lane faded efficient trends and also failed. This candidate asks a different current-data question: after volatility is already high, does a bounded pullback inside an established EMA trend create cleaner continuation than either compression breakout or trend exhaustion fading?

It is independent from level-and-pullback candidates because it does not reference round numbers, prior highs/lows, session extremes, broken levels, or retest acceptance.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- max consecutive zero-trade months exceeds 3
- cost sensitivity fails under p95 measured spread
- any broker family is materially negative across cost models
- any future edit changes thresholds after seeing first-pass matrix results

This candidate must not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution unless the matrix first-pass gate is satisfied.
