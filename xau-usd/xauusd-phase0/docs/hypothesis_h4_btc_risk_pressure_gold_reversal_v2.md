# H4 BTC Risk Pressure Gold Reversal v2 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v2
Author / owner: maksoftwares / Codex

Expected trade count per year: 20-160
Expected cost-adjusted PF: 1.00-1.50
Expected losing-month percentage: 35%-82%
Expected worst single month: -6R to -20R
Expected max consecutive zero months: 4
Expected R-multiple distribution: intermediate-frequency H4 reversal losses near -1R with fewer 1.45R wins after higher-quality shifted BTC stress.

## Mechanical Definition

Expert: `h4_btc_risk_pressure_gold_reversal_v2`

This is a new disabled Phase 0R research candidate. It is not an edit to rejected v0 or v1. It tests an intermediate version between sparse v0 and over-broadened v1: keep v0-style EMA-side and reversal-candle quality, but use one signal per UTC day per direction and slightly less extreme BTC stress thresholds.

Data source:

- BTC-USD daily OHLCV proxy from Yahoo Finance at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC features are shifted by one completed daily observation before being merged into XAU H4 decisions.
- XAUUSD H4 bars from the existing broker matrix windows.

Feature construction:

1. Calculate shifted BTC 5-day log return, 20-day log return, 126-day z-score of BTC 5-day return, 252-day percentile rank of absolute BTC 5-day return, and 126-day z-score of log BTC volume.
2. Calculate XAU H4 ATR(14), EMA(40), 3-bar log return, and 6-bar log return.
3. BTC pressure is active only when all are true:
   - `abs(btc_return_5d) >= 0.080`
   - `abs(btc_return_z126) >= 0.40`
   - `btc_abs_return_percentile252 >= 0.60`
   - `btc_volume_z126 >= 0.00`
4. Short setup:
   - BTC 5-day return is negative and at or below `-0.080`.
   - XAU H4 has locally overextended upward: `h4_return_3 >= 0.0030`.
   - XAU H4 6-bar return is not an extreme runaway: `h4_return_6 <= 0.0575`.
   - Close is above EMA(40).
   - Completed H4 candle is bearish and closes in the lower 48% of its range.
   - Close is no more than 3.10 ATR above EMA(40).
5. Long setup:
   - BTC 5-day return is positive and at or above `+0.080`.
   - XAU H4 has locally overextended downward: `h4_return_3 <= -0.0030`.
   - XAU H4 6-bar return is not an extreme runaway: `h4_return_6 >= -0.0575`.
   - Close is below EMA(40).
   - Completed H4 candle is bullish and closes in the upper 48% of its range.
   - Close is no more than 3.10 ATR below EMA(40).
6. Use at most one signal per UTC day per direction.
7. Entry is next simulated market entry after the completed H4 signal bar.
8. Stop is 1.35 times H4 ATR(14) beyond the signal close.
9. Target is 1.45R.
10. Planned time stop is 6 completed H4 bars.

Implementation mapping:

- Strategy: `src/phase0/strategies/h4_btc_risk_pressure_gold_reversal_v2.py`
- BTC data loader: `src/phase0/btc_risk_pressure_data.py`
- Synthetic fixture: `src/phase0/synthetic.py::_h4_btc_risk_pressure_gold_reversal_context`
- Test: `tests/test_h4_btc_risk_pressure_gold_reversal_v2.py`

## Expected Behavior

The v2 candidate should produce more observations than v0 without the large cross-broker dilution seen in v1. It should preserve the delayed-exhaustion BTC/XAU thesis and use H4 ATR stops to keep measured P95 spread from dominating the R profile.

It should win only if the sparse v0 edge persists when weekly throttling is relaxed and BTC stress quality remains high enough. It should fail if the extra observations dilute PF, if Dukascopy remains negative, or if activity is still too low.

## Why This Hypothesis Should Exist

The v0 result was too sparse but had 9/9 PF cells above 1.30. The v1 result increased activity in two broker windows but diluted PF and failed Dukascopy. This v2 asks a narrower follow-up question: can daily throttling and a mild stress-threshold adjustment increase evidence while preserving v0's stricter structural filters?

This remains independent from retest, round-number, GLD-flow, COT, futures-volume, and FX-rotation candidates because it uses shifted BTC daily pressure plus completed H4 XAU exhaustion/reversal structure.

## What Would Falsify It

Reject v2 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- max consecutive zero-trade months exceeds 4
- cost sensitivity fails under p95 measured spread
- BTC features are not shifted before XAU H4 decisions
- Dukascopy fails materially while Capital.com or Pepperstone carries the result
- any future edit changes thresholds after seeing first-pass matrix results

This candidate must not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution unless the matrix first-pass gate is satisfied.
