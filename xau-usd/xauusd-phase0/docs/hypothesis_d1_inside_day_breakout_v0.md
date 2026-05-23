# D1 Inside-Day Breakout v0 Hypothesis

Hypothesis date: 2026-05-24
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: D1 compression breakout
Entry / decision timeframe: D1 state and H4 signal timestamp, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 72-576
Expected median hold hours: 6-48
Expected decisions per week: 0-2
Timeframe diversification qualifies: yes
Expected trade count per year: 30-120
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many failed breakouts near -1R, fewer +1.5R expansions, and no acceptable pass if one compression episode dominates the result.

## Mechanical Definition

This candidate is a bidirectional D1 inside-day compression breakout expert. It is not a breakout-retest, fixed-level reclaim, weekly-open, round-number, VWAP, session-extreme, or M5 impulse strategy. It tests whether a daily inside day creates enough compression that the next H4 close outside the mother-day range has continuation value.

The mechanical setup is:

1. Market and decision timeframe: XAUUSD with D1 inside-day state and H4 completed-candle decisions. M5 bars are used only by the existing simulator for market-entry and exit sequencing.
2. Inside-day definition: latest completed D1 candle has high less than or equal to the previous D1 high, low greater than or equal to the previous D1 low, and range no more than 70% of the previous D1 range.
3. Mother-day quality: previous D1 range must be at least 0.75 times the previous D1 ATR(14).
4. Active window: after a qualifying inside day closes, search only the first 48 hours of completed H4 bars.
5. Long breakout: H4 candle closes above the mother-day high by at least 0.05 times H4 ATR(14), closes bullish, body is at least 35% of range, and closes in the upper 35% of the candle.
6. Short breakout: H4 candle closes below the mother-day low by at least 0.05 times H4 ATR(14), closes bearish, body is at least 35% of range, and closes in the lower 35% of the candle.
7. Frequency control: take at most one long and one short setup per inside-day candle.
8. Entry: enter at the first available M5 execution bar at or after the completed H4 signal timestamp, using the existing Phase 0 cost model and one-position-at-a-time rule.
9. Stop: for long setups, stop below the inside-day low by 0.25 times H4 ATR(14). For short setups, stop above the inside-day high by 0.25 times H4 ATR(14).
10. Target: fixed 1.5R.
11. Invalidation: no setup if D1/H4 indicators are unavailable, the inside day is missing, the H4 breakout candle quality fails, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is lower-frequency expansion after daily compression. The candidate should produce fewer trades than M5 retest systems and should not rely on repeated intraday level retests. It should lose when XAU false-breaks the mother-day range or mean-reverts immediately after expansion.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- The candidate should provide genuine timeframe diversification only if median hold time exceeds 24 hours and yearly trade count remains below 100.

## Why This Hypothesis Should Exist

Inside days represent daily-range contraction. When gold breaks out of the mother-day range on a decisive H4 close, resting stop orders and momentum participants may create follow-through. This hypothesis tests compression expansion directly, without requiring a retest or a pullback to the broken level.

The hypothesis should only pass if the behavior survives different brokers, cost assumptions, and time windows. If it is only positive in one venue, one side, or one compression episode, it should be rejected.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- The candidate only passes through one or two unusually large expansion episodes.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds breakout-retest, round-number, session-extreme, or discretionary news filters after results are known.

Code mapping after implementation:

- D1 inside-day feature construction: `src/phase0/strategies/d1_inside_day_breakout_v0.py::D1InsideDayBreakoutV0Strategy.prepare_features`
- D1 inside-day state: `src/phase0/strategies/d1_inside_day_breakout_v0.py::D1InsideDayBreakoutV0Strategy._inside_day_at_timestamp`
- H4 breakout trigger: `src/phase0/strategies/d1_inside_day_breakout_v0.py::D1InsideDayBreakoutV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/d1_inside_day_breakout_v0.py::D1InsideDayBreakoutV0Strategy.build_trade_plan`
