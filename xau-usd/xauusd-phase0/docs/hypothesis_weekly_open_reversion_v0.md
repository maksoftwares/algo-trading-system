# Weekly Open Reversion v0 Hypothesis

Hypothesis date: 2026-05-24
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: weekly open mean reversion
Entry / decision timeframe: M15 signal timestamp, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 24-288
Expected median hold hours: 2-24
Expected decisions per week: 0-2
Timeframe diversification qualifies: no
Expected trade count per year: 40-180
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-65%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Mostly -1R failed fades, fewer variable-R wins back to weekly open, and no acceptable pass if one week dominates total profit.

## Mechanical Definition

This candidate is a bidirectional XAUUSD weekly-open mean-reversion expert. It is not a breakout-retest, retest-hold, round-number, swing-breakout, VWAP, fixed session-extreme, or momentum-continuation strategy. It tests whether large same-week displacements away from the weekly open tend to mean-revert after an M15 rejection candle.

The mechanical setup is:

1. Market and decision timeframe: XAUUSD with M15 completed-candle decisions. M5 bars are used only by the existing simulator for market-entry and exit sequencing.
2. Weekly reference: the weekly open is the first M15 open of the ISO week. It is available from the first completed M15 bar of the week and must not be recalculated with later data.
3. Active window: do not trade before the first 96 M15 bars of the week have completed. Do not trade after M15 week bar index 430.
4. Session window: only trade M15 bars whose UTC bar-start time is at or after 07:00 and before 20:00.
5. Long setup: close is at least 2.25 times M15 ATR(14) below the weekly open, the candle closes bullish, body is at least 25% of range, close is in the upper 35% of the candle, and lower wick is at least 20% of range.
6. Short setup: close is at least 2.25 times M15 ATR(14) above the weekly open, the candle closes bearish, body is at least 25% of range, close is in the lower 35% of the candle, and upper wick is at least 20% of range.
7. Frequency control: take at most one long and one short signal per ISO week.
8. Entry: enter at the first available M5 execution bar at or after the completed M15 signal timestamp, using the existing Phase 0 cost model and one-position-at-a-time rule.
9. Stop: for long setups, stop below the M15 rejection candle low by 0.35 times M15 ATR(14). For short setups, stop above the M15 rejection candle high by 0.35 times M15 ATR(14).
10. Target: target the weekly open.
11. Risk filter: reject any setup where estimated reward to the weekly open is less than 1.15 times estimated stop risk.
12. Invalidation: no setup if ATR, weekly open, candle range, stop, or target construction is unavailable or creates non-positive risk/reward.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is lower frequency than the approved breakout-retest family and should cluster around weeks where gold extends rapidly away from the weekly open. It should lose during strong one-way repricing weeks that never rotate back toward the weekly open.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- The candidate should not be counted as same-family with breakout-retest because there is no break, retest, hold, or continuation trigger.

## Why This Hypothesis Should Exist

Gold often overshoots around session flows and macro repricing, then partially rotates toward widely watched weekly reference prices when the immediate pressure fades. The weekly open is a simple anchor that many discretionary and systematic traders monitor. This candidate tests whether that anchor has enough mean-reversion pull after a large displacement and visible M15 rejection.

The hypothesis should only pass if the mean-reversion behavior survives different brokers, cost assumptions, and time windows. If it depends on one unusually clean period, one broker, or one side of the market, it should be rejected.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- The candidate only passes through one or two unusually large weekly reversions.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds breakout-retest, round-number, session-extreme, or discretionary news filters after results are known.

Code mapping after implementation:

- Weekly-open feature construction: `src/phase0/strategies/weekly_open_reversion_v0.py::WeeklyOpenReversionV0Strategy.prepare_features`
- M15 rejection trigger: `src/phase0/strategies/weekly_open_reversion_v0.py::WeeklyOpenReversionV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/weekly_open_reversion_v0.py::WeeklyOpenReversionV0Strategy.build_trade_plan`
