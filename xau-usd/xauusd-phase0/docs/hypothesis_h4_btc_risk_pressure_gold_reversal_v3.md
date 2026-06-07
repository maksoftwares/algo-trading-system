# H4 BTC Risk Pressure Gold Reversal v3 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v3
Author / owner: maksoftwares / Codex

Expected trade count per year: 20-180
Expected cost-adjusted PF: 1.00-1.55
Expected losing-month percentage: 35%-82%
Expected worst single month: -6R to -20R
Expected max consecutive zero months: 4
Expected R-multiple distribution: clustered H4 reversal losses near -1R with occasional 1.45R wins after shifted BTC stress clusters and completed XAU rejection candles.

## Mechanical Definition

Expert: `h4_btc_risk_pressure_gold_reversal_v3`

This is a new disabled Phase 0R research candidate. It is not an edit to rejected v0, v1, or v2. It tests whether the sparse but high-PF BTC stress-reversal clue from v0 survives when BTC pressure is defined as a clustered regime rather than a single extreme 5-day shock.

Data source:

- BTC-USD daily OHLCV proxy from Yahoo Finance at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC features are shifted by one completed daily observation before being merged into XAU H4 decisions.
- XAUUSD H4 bars from the existing broker matrix windows.

Feature construction:

1. Calculate shifted BTC 5-day log return, 20-day log return, 126-day z-score of BTC 5-day return, 252-day percentile rank of absolute BTC 5-day return, and 126-day z-score of log BTC volume.
2. Calculate XAU H4 ATR(14), EMA(40), EMA(80), 3-bar log return, 6-bar log return, and 12-bar log return.
3. BTC clustered pressure is active only when all are true:
   - `abs(btc_return_5d) >= 0.060`
   - `abs(btc_return_20d) >= 0.105`
   - `btc_return_5d` and `btc_return_20d` have the same sign
   - `abs(btc_return_z126) >= 0.35`
   - `btc_abs_return_percentile252 >= 0.58`
   - `btc_volume_z126 >= -0.05`
4. Short setup:
   - BTC 5-day return is negative and at or below `-0.060`.
   - BTC 20-day return is negative and at or below `-0.105`.
   - XAU H4 has locally overextended upward: `h4_return_3 >= 0.0028`.
   - XAU H4 6-bar return is positive but not a runaway: `0.0020 <= h4_return_6 <= 0.0600`.
   - XAU H4 12-bar return is not above `0.0800`.
   - Close is above EMA(40).
   - Completed H4 candle is bearish and closes in the lower 48% of its range.
   - Close is between 0.10 and 3.15 ATR above EMA(40).
   - Close is no more than 4.00 ATR above EMA(80).
5. Long setup:
   - BTC 5-day return is positive and at or above `+0.060`.
   - BTC 20-day return is positive and at or above `+0.105`.
   - XAU H4 has locally overextended downward: `h4_return_3 <= -0.0028`.
   - XAU H4 6-bar return is negative but not a runaway: `-0.0600 <= h4_return_6 <= -0.0020`.
   - XAU H4 12-bar return is not below `-0.0800`.
   - Close is below EMA(40).
   - Completed H4 candle is bullish and closes in the upper 48% of its range.
   - Close is between 0.10 and 3.15 ATR below EMA(40).
   - Close is no more than 4.00 ATR below EMA(80).
6. Use at most one signal per two-day bucket per direction.
7. Entry is next simulated market entry after the completed H4 signal bar.
8. Stop is 1.40 times H4 ATR(14) beyond the signal close.
9. Target is 1.45R.
10. Planned time stop is 6 completed H4 bars.

Implementation mapping:

- Strategy: `src/phase0/strategies/h4_btc_risk_pressure_gold_reversal_v3.py`
- BTC data loader: `src/phase0/btc_risk_pressure_data.py`
- Synthetic fixture: `src/phase0/synthetic.py::_h4_btc_risk_pressure_gold_reversal_context`
- Test: `tests/test_h4_btc_risk_pressure_gold_reversal_v3.py`

## Expected Behavior

The v3 candidate should produce more observations than sparse v0 while preserving more BTC signal quality than v1. It should behave like an H4 exhaustion/reversal strategy during multi-day BTC stress clusters, not like a generic BTC/gold correlation trade.

It should win only if same-sign 5-day and 20-day BTC pressure clusters create delayed XAU overextension that reverses after a completed H4 rejection candle. It should fail if the clustered definition is still too sparse, if extra opportunities dilute PF, or if broker windows split materially.

## Why This Hypothesis Should Exist

The v0 result was too sparse but had 9/9 PF cells above 1.30. The v1 result broadened activity but diluted PF and failed Dukascopy. The v2 result stayed too sparse and fragmented. This v3 asks a different question: can a same-sign BTC stress cluster keep the high-quality part of v0 while creating enough H4 rejection opportunities to be reviewable?

This remains independent from retest, round-number, GLD-flow, COT, futures-volume, and FX-rotation candidates because it uses shifted BTC daily pressure plus completed H4 XAU exhaustion/reversal structure.

## What Would Falsify It

Reject v3 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- fewer than 7 of 9 matrix cells reach the 40-trade floor
- concentration gates fail
- max consecutive zero-trade months exceeds 4
- cost sensitivity fails under p95 measured spread
- BTC features are not shifted before XAU H4 decisions
- one broker or cost model carries the result while another broker is materially negative
- any future edit changes thresholds after seeing first-pass matrix results

This candidate must not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution unless the matrix first-pass gate is satisfied.
