# H1 BTC Risk Pressure Gold Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex

Expected trade count per year: 40-220
Expected cost-adjusted PF: 0.95-1.45
Expected losing-month percentage: 35%-80%
Expected worst single month: -6R to -22R
Expected max consecutive zero months: 4
Expected R-multiple distribution: moderate-frequency H1 reversal losses near -1R with fewer 1.45R wins after shifted BTC pressure extremes.

## Mechanical Definition

Expert: `h1_btc_risk_pressure_gold_reversal_v0`

This is a disabled Phase 0R research candidate. It tests whether shifted daily BTC-USD stress can identify cross-asset risk episodes where H1 XAUUSD temporarily overreacts and then mean-reverts. It is not an edit to rejected H1 BTC follow-through or H4 BTC reversal candidates.

Data source:

- BTC-USD daily OHLCV proxy from Yahoo Finance at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC features are shifted by one completed daily observation before being merged into XAU H1 decisions.
- XAUUSD H1 and M5 bars come from the existing broker matrix windows.

Feature construction:

1. Calculate shifted BTC 5-day log return, 20-day log return, 126-day z-score of BTC 5-day return, 252-day percentile rank of absolute BTC 5-day return, and 126-day z-score of log BTC volume.
2. Calculate XAU H1 ATR(14), EMA(50), 6-bar log return, and 12-bar log return.
3. BTC pressure is active only when all are true:
   - `abs(btc_return_5d) >= 0.080`
   - `abs(btc_return_z126) >= 0.45`
   - `btc_abs_return_percentile252 >= 0.65`
   - `btc_volume_z126 >= 0.10`
4. Evaluate only completed H1 bars ending at 08:00, 12:00, 16:00, or 20:00 UTC.
5. Short setup:
   - BTC 5-day return is negative and at or below `-0.080`.
   - XAU has locally overextended upward: `h1_return_12 >= 0.0030` and `h1_return_6 >= 0.0012`.
   - Close is above EMA(50).
   - Completed H1 candle is bearish and closes in the lower 48% of its range.
   - Close is no more than 3.60 ATR above EMA(50).
6. Long setup:
   - BTC 5-day return is positive and at or above `+0.080`.
   - XAU has locally overextended downward: `h1_return_12 <= -0.0030` and `h1_return_6 <= -0.0012`.
   - Close is below EMA(50).
   - Completed H1 candle is bullish and closes in the upper 48% of its range.
   - Close is no more than 3.60 ATR below EMA(50).
7. Use at most one signal per UTC day per direction.
8. Entry is next simulated market entry after the completed H1 signal bar.
9. Stop is 1.20 times H1 ATR(14) beyond the signal close.
10. Target is 1.45R.
11. Planned time stop is 18 completed H1 bars.

Implementation mapping:

- Strategy: `src/phase0/strategies/h1_btc_risk_pressure_gold_reversal_v0.py`
- BTC data loader: `src/phase0/btc_risk_pressure_data.py`
- Synthetic fixture: `src/phase0/synthetic.py::_h1_btc_risk_pressure_gold_reversal_context`
- Test: `tests/test_h1_btc_risk_pressure_gold_reversal_v0.py`

## Expected Behavior

This candidate should produce more observations than the H4 BTC reversal variants while avoiding the rejected H1 follow-through thesis. It should make money only if BTC stress episodes create short-lived XAU safe-haven or risk-on overreactions that reverse on completed H1 rejection bars.

Useful evidence would require broad broker persistence, p95 cost survivability, and enough trades in every matrix cell. A Pepperstone-only or Dukascopy-only pocket is not enough.

## Why This Hypothesis Should Exist

Prior BTC work gave two distinct clues:

- H1 BTC follow-through failed with enough trades but no PF persistence.
- H4 BTC reversal v0 reached 9/9 PF cells above 1.30 but was too sparse, while broader H4 v1/v2 variants failed persistence or activity.

This candidate asks a fresh question: can H1 rejection timing create enough activity while preserving the delayed BTC/XAU reversal idea? It remains independent from retest, round-number, GLD-flow, COT, futures-volume, and FX-rotation candidates because it uses shifted BTC daily pressure plus completed H1 XAU overreaction/rejection structure.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- max consecutive zero-trade months exceeds 4
- cost sensitivity fails under p95 measured spread
- BTC features are not shifted before XAU H1 decisions
- any broker family is materially negative across cost models
- any future edit changes thresholds after seeing first-pass matrix results

This candidate must not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution unless the matrix first-pass gate is satisfied.
