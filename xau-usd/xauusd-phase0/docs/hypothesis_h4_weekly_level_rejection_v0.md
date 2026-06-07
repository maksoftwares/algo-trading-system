# H4 Weekly Level Rejection v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex

Expected trade count per year: 10-70
Expected cost-adjusted PF: 1.00-1.55
Expected losing-month percentage: 35%-85%
Expected worst single month: -5R to -18R
Expected max consecutive zero months: 4
Expected R-multiple distribution: low-frequency H4 rejection losses near -1R with occasional 1.65R wins after failed acceptance beyond previous completed weekly extremes.

## Mechanical Definition

Expert: `h4_weekly_level_rejection_v0`

This is a disabled Phase 0R research candidate. It tests whether previous completed weekly high/low rejection on H4 creates a lower-frequency, wider-stop edge that is distinct from M5/M15 breakout-retest execution.

Data source:

- XAUUSD D1 bars from each broker matrix window.
- XAUUSD H4 bars from each broker matrix window.
- Weekly levels are derived mechanically from completed D1 bars only. No native W1 feed is required.

Feature construction:

1. Aggregate D1 bars by ISO week.
2. For each completed week, compute weekly high, low, close, and range.
3. For each H4 bar, merge only the latest completed weekly record and expose the previous completed weekly high/low/range.
4. Compute H4 ATR(14).
5. Reject any setup where previous-week range is less than 1.50 H4 ATR or the signal H4 candle range is less than 0.55 H4 ATR.

Short setup:

- H4 high sweeps at least 0.10 ATR above previous completed weekly high.
- H4 close finishes at least 0.05 ATR back below previous completed weekly high.
- H4 candle closes below its open.
- H4 close is in the lower 45% of its range.

Long setup:

- H4 low sweeps at least 0.10 ATR below previous completed weekly low.
- H4 close finishes at least 0.05 ATR back above previous completed weekly low.
- H4 candle closes above its open.
- H4 close is in the upper 45% of its range.

Execution:

1. Use at most one signal per ISO week per direction.
2. Entry is next simulated market entry after the completed H4 signal bar.
3. Stop is 0.35 H4 ATR beyond the rejection candle high/low.
4. Target is 1.65R.

Implementation mapping:

- Strategy: `src/phase0/strategies/h4_weekly_level_rejection_v0.py`
- Synthetic fixture: `src/phase0/synthetic.py::_h4_weekly_level_rejection_context`
- Test: `tests/test_h4_weekly_level_rejection_v0.py`

## Expected Behavior

This candidate should trade much less often than M5 retest strategies and should have wider average stop distance, reducing measured-spread dominance. It should win only if failed acceptance outside widely visible weekly extremes reliably reverses on completed H4 candles across broker datasets.

It should fail if weekly high/low rejection is just another level-touch story without durable post-cost expectancy, if trade count is too sparse, or if one broker carries the result.

## Why This Hypothesis Should Exist

The Phase 0R lower-cost plan still lists weekly level rejection with H4 confirmation as not registered. It is current-data feasible and slower than the cost-suspended breakout-retest family. Although it uses levels, it does not require a breakout/retest state machine, M5 trigger, or broken support/resistance continuation.

This is not a rescue filter for `breakout_retest` and it is not a same-family approval claim. It is a fresh, slower, completed-candle rejection hypothesis.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- fewer than 7 of 9 matrix cells reach the 40-trade floor
- max consecutive zero-trade months exceeds 4
- concentration gates fail
- one broker/cost pocket carries the result
- measured P95 spread would exceed 0.30R for typical trades
- any future edit changes thresholds after seeing first-pass matrix results

This candidate must not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution unless the matrix first-pass gate is satisfied.
