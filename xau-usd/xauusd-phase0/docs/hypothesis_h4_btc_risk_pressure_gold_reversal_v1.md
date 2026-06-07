# H4 BTC Risk Pressure Gold Reversal v1 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v1
Author / owner: maksoftwares / Codex

Expected trade count per year: 35-220
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 35%-82%
Expected worst single month: -6R to -22R
Expected max consecutive zero months: 4
Expected R-multiple distribution: broader H4 reversal losses near -1R with occasional 1.40R wins after shifted BTC stress and completed XAU rejection candles.

## Mechanical Definition

Expert: `h4_btc_risk_pressure_gold_reversal_v1`

This is a new disabled Phase 0R research candidate. It is not a modification of the rejected v0 after result-producing evidence. It broadens activity before its own registration by relaxing the BTC stress threshold, using one signal per day per direction, and treating EMA(40) as a distance context rather than a hard side-of-EMA filter.

Data source:

- BTC-USD daily OHLCV proxy from Yahoo Finance at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC features are shifted by one completed daily observation before being merged into XAU H4 decisions.
- XAUUSD H4 bars from the existing broker matrix windows.

Feature construction:

1. Calculate shifted BTC 5-day log return, 20-day log return, 126-day z-score of BTC 5-day return, 252-day percentile rank of absolute BTC 5-day return, and 126-day z-score of log BTC volume.
2. Calculate XAU H4 ATR(14), EMA(40), 3-bar log return, and 6-bar log return.
3. BTC pressure is active only when all are true:
   - `abs(btc_return_5d) >= 0.065`
   - `abs(btc_return_z126) >= 0.30`
   - `btc_abs_return_percentile252 >= 0.55`
   - `btc_volume_z126 >= -0.15`
4. Short setup:
   - BTC 5-day return is negative and at or below `-0.065`.
   - XAU H4 has locally overextended upward: `h4_return_3 >= 0.0025`.
   - XAU H4 6-bar return is not an extreme runaway: `h4_return_6 <= 0.0600`.
   - Completed H4 candle is bearish and closes in the lower 50% of its range.
   - Close is no more than 3.25 ATR above EMA(40).
5. Long setup:
   - BTC 5-day return is positive and at or above `+0.065`.
   - XAU H4 has locally overextended downward: `h4_return_3 <= -0.0025`.
   - XAU H4 6-bar return is not an extreme runaway: `h4_return_6 >= -0.0600`.
   - Completed H4 candle is bullish and closes in the upper 50% of its range.
   - Close is no more than 3.25 ATR below EMA(40).
6. Use at most one signal per UTC day per direction.
7. Entry is next simulated market entry after the completed H4 signal bar.
8. Stop is 1.30 times H4 ATR(14) beyond the signal close.
9. Target is 1.40R.
10. Planned time stop is 6 completed H4 bars.

Implementation mapping:

- Strategy: `src/phase0/strategies/h4_btc_risk_pressure_gold_reversal_v1.py`
- BTC data loader: `src/phase0/btc_risk_pressure_data.py`
- Synthetic fixture: `src/phase0/synthetic.py::_h4_btc_risk_pressure_gold_reversal_context`
- Test: `tests/test_h4_btc_risk_pressure_gold_reversal_v1.py`

## Expected Behavior

The v1 candidate should produce materially more trades than v0 while preserving the same delayed-exhaustion thesis. It should still be lower frequency than H1 follow-through variants and should keep measured P95 spread from dominating R because it uses H4 ATR stops.

It should win if BTC stress creates delayed, tradable exhaustion in XAU after a completed H4 rejection candle. It should lose if the v0 PF strength was only sparse luck, if broader sampling dilutes the effect, or if BTC pressure does not transfer across broker windows.

## Why This Hypothesis Should Exist

The locked v0 result was rejected but produced a rare high-quality clue: 9/9 PF cells above 1.30 with all p95 cells passing. Its failure mode was not PF persistence; it was sample size and activity. A pre-registered v1 broadening attempt is justified because it tests whether the same BTC stress-reversal behavior survives with enough observations to be reviewable.

This remains independent from level-and-pullback, round-number retest, GLD-flow, COT, futures-volume, and FX-rotation candidates because it uses shifted BTC daily pressure plus completed H4 XAU reversal structure.

## What Would Falsify It

Reject v1 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- max consecutive zero-trade months exceeds 4
- cost sensitivity fails under p95 measured spread
- BTC features are not shifted before XAU H4 decisions
- the broader sample dilutes PF into one-broker strength or one-window strength
- any future edit changes thresholds after seeing first-pass matrix results

This candidate must not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution unless the matrix first-pass gate is satisfied.
