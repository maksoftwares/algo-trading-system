# H4 BTC Risk Pressure Gold Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex

Expected trade count per year: 12-120
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 35%-80%
Expected worst single month: -5R to -18R
Expected max consecutive zero months: 4
Expected R-multiple distribution: sparse H4 reversal losses near -1R with fewer 1.45R wins after BTC stress extremes and local XAU exhaustion.

## Mechanical Definition

Expert: `h4_btc_risk_pressure_gold_reversal_v0`

This is a disabled Phase 0R research candidate. It tests H4 XAUUSD reversal after shifted BTC-USD daily stress extremes. It is not an edit to `h1_btc_risk_pressure_gold_followthrough_v0`, v1, or v2, and it is not a retest/round-number/level candidate.

Data source:

- BTC-USD daily OHLCV proxy from Yahoo Finance at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC features are shifted by one completed daily observation before being merged into XAU H4 decisions.
- XAUUSD H4 bars from the existing broker matrix windows.

Feature construction:

1. Calculate shifted BTC 5-day log return, 20-day log return, 126-day z-score of BTC 5-day return, 252-day percentile rank of absolute BTC 5-day return, and 126-day z-score of log BTC volume.
2. Calculate XAU H4 ATR(14), EMA(40), 3-bar log return, and 6-bar log return.
3. BTC pressure is active only when all are true:
   - `abs(btc_return_5d) >= 0.090`
   - `abs(btc_return_z126) >= 0.45`
   - `btc_abs_return_percentile252 >= 0.65`
   - `btc_volume_z126 >= 0.15`
4. Short setup:
   - BTC 5-day return is negative and at or below `-0.090`.
   - XAU H4 has locally overextended upward: `h4_return_3 >= 0.0035`.
   - XAU H4 6-bar return is not an extreme runaway: `h4_return_6 <= 0.0550`.
   - Close is above EMA(40).
   - Completed H4 candle is bearish and closes in the lower 45% of its range.
   - Close is no more than 3.00 ATR above EMA(40).
5. Long setup:
   - BTC 5-day return is positive and at or above `+0.090`.
   - XAU H4 has locally overextended downward: `h4_return_3 <= -0.0035`.
   - XAU H4 6-bar return is not an extreme runaway: `h4_return_6 >= -0.0550`.
   - Close is below EMA(40).
   - Completed H4 candle is bullish and closes in the upper 45% of its range.
   - Close is no more than 3.00 ATR below EMA(40).
6. Use at most one signal per ISO week per direction.
7. Entry is next simulated market entry after the completed H4 signal bar.
8. Stop is 1.35 times H4 ATR(14) beyond the signal close.
9. Target is 1.45R.
10. Planned time stop is 6 completed H4 bars.

Implementation mapping:

- Strategy: `src/phase0/strategies/h4_btc_risk_pressure_gold_reversal_v0.py`
- BTC data loader: `src/phase0/btc_risk_pressure_data.py`
- Synthetic fixture: `src/phase0/synthetic.py::_h4_btc_risk_pressure_gold_reversal_context`
- Test: `tests/test_h4_btc_risk_pressure_gold_reversal_v0.py`

## Expected Behavior

The candidate should fire rarely, only after large BTC pressure events have already pushed local H4 XAU structure into a stretched state. The expected edge is not BTC-to-gold continuation. It is delayed exhaustion: BTC drawdowns can coincide with short-lived safe-haven gold bids that fade after an H4 rejection candle, and BTC upside shocks can coincide with short-lived gold weakness that fades after an H4 reclaim candle.

The wide H4 stop is intended to keep measured P95 spread below the Phase 0R cost-fragility threshold. The candidate should lose during genuine gold trend continuation and during BTC pressure events that have no independent information for XAU.

## Why This Hypothesis Should Exist

The prior BTC lane tested H1 follow-through and failed cross-broker persistence. This v0 asks a different question: whether BTC stress is useful as a delayed H4 exhaustion context rather than an immediate H1 continuation trigger.

The candidate remains independent from the approved level-and-pullback family because it does not use retests, round numbers, session levels, swing levels, or breakout acceptance. It uses shifted BTC daily pressure plus completed H4 rejection/extension state.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades unless a separately registered low-frequency exception exists
- concentration gates fail
- max consecutive zero-trade months exceeds 4
- cost sensitivity fails under p95 measured spread
- BTC features are not shifted before XAU H4 decisions
- results are broker-specific or carried by one narrow time window
- any future edit changes thresholds after seeing first-pass matrix results

This candidate must not be promoted to Phase 1, Phase 2, demo, paper execution, or live execution unless it passes the full Phase 0 research sequence and receives explicit owner approval.
