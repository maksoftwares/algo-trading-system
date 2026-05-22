# Opening Drive Failed Continuation v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 60-220
Expected cost-adjusted PF: 1.05-1.40
Expected losing-month percentage: 40%-60%
Expected worst single month: -10R to -22R
Expected max consecutive zero months: 1
Expected R-multiple distribution: Many failed reversals near -1R, fewer +1.5R winners, and no acceptable pass if one month or one trade dominates total profit.

## Mechanical Definition

This candidate is a bidirectional XAUUSD opening-drive failure expert intended to test whether the first New York drive often overextends and then fails to continue. It is a session-failure idea, not a level break-and-retest idea.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries and M5 opening-drive context.
2. Opening drive window: use completed M5 bars whose bar start time is from 13:30 UTC through 13:55 UTC. This fixed UTC window is used for v0 to avoid discretionary daylight-saving adjustments.
3. Failure window: only completed M5 bars whose bar start time is from 14:00 UTC through 15:55 UTC are eligible for a failed-continuation trigger.
4. Opening drive range: drive high is the maximum high in the opening-drive window, drive low is the minimum low, drive open is the first open, and drive close is the final close.
5. Drive qualification: opening-drive range must be at least 1.0 times current M5 ATR(14) and no more than 8.0 times current M5 ATR(14). Opening-drive body must be at least 35% of drive range.
6. Bearish failed continuation: if the opening drive closes above its open, a later M5 candle must trade at least 0.10 times M5 ATR(14) above the drive high, then close back at least 0.05 times M5 ATR(14) below the drive high. The failure candle must be bearish, have body at least 35% of its range, and close in the lower 45% of its range.
7. Bullish failed continuation: if the opening drive closes below its open, a later M5 candle must trade at least 0.10 times M5 ATR(14) below the drive low, then close back at least 0.05 times M5 ATR(14) above the drive low. The failure candle must be bullish, have body at least 35% of its range, and close in the upper 45% of its range.
8. Entry: enter at the next eligible M5 open after the failure candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
9. Stop: for long setups, place the stop below the failure low or opening-drive low by an additional 0.25 times M5 ATR(14), whichever creates the wider protective distance. For short setups, place the stop above the failure high or opening-drive high by an additional 0.25 times M5 ATR(14), whichever creates the wider protective distance.
10. Target: use a fixed 1.5R target.
11. Frequency control: take at most one setup per UTC session day.
12. Invalidation: no setup if the opening drive is incomplete, the drive range/body qualification fails, the failure candle occurs outside the fixed failure window, the candle fails the quality rule, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is moderate frequency with most opportunities near the first New York continuation attempt. The strategy should capture overextension/failure after an initial directional drive and should not need H1 trend, retest, or prior-level logic to work.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer should be plausible because opening-drive failure is a session microstructure behavior, though XAUUSD may remain the strongest expression.

## Why This Hypothesis Should Exist

The first New York impulse can reflect short-term positioning pressure rather than durable continuation. When that impulse attempts a continuation beyond the opening-drive extreme and closes back inside, trapped continuation traders may create a mean-reverting move. The candidate tests that failure behavior mechanically with no retest requirement and no discretionary news filter.

This is independent from `breakout_retest` and `swing_breakout_retest_v0`, which both wait for a break and retest of structural levels. This candidate uses only same-session opening-drive failure mechanics.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Manual adversarial review finds logic gaps above the allowed threshold.
- The strategy only passes after adding discretionary time, news, trend, volatility, or candle filters after results are known.

Code mapping after implementation:

- Opening-drive feature construction: `src/phase0/strategies/opening_drive_failed_continuation_v0.py::OpeningDriveFailedContinuationV0Strategy.prepare_features`
- Failed-continuation trigger: `src/phase0/strategies/opening_drive_failed_continuation_v0.py::OpeningDriveFailedContinuationV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/opening_drive_failed_continuation_v0.py::OpeningDriveFailedContinuationV0Strategy.build_trade_plan`
