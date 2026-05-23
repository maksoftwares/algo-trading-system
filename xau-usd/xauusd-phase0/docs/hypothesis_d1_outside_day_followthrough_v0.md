# D1 Outside-Day Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-24
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: D1 outside-day momentum follow-through
Entry / decision timeframe: D1 state and H4 signal timestamp, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 48-432
Expected median hold hours: 4-36
Expected decisions per week: 0-2
Timeframe diversification qualifies: yes
Expected trade count per year: 40-140
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many failed continuation attempts near -1R, fewer +1.5R follow-through winners, and no acceptable pass if one outside-day episode dominates the result.

## Mechanical Definition

This candidate is a bidirectional D1 outside-day follow-through expert. It is not a breakout-retest, fixed-level reclaim, inside-day compression, weekly-open, round-number, VWAP, session-extreme, or M5 impulse strategy. It tests whether a decisive daily outside bar with a directional close tends to continue on the next H4 confirmation candle.

The mechanical setup is:

1. Market and decision timeframe: XAUUSD with D1 outside-day state and H4 completed-candle decisions. M5 bars are used only by the existing simulator for market-entry and exit sequencing.
2. Outside-day definition: latest completed D1 candle has high greater than or equal to the previous D1 high, low less than or equal to the previous D1 low, range at least 1.00 times D1 ATR(14), and body at least 35% of its range.
3. Long outside day: D1 close is above D1 open and closes in the upper 30% of the candle range.
4. Short outside day: D1 close is below D1 open and closes in the lower 30% of the candle range.
5. Active window: after a qualifying outside day closes, search only the first 24 hours of completed H4 bars.
6. Long follow-through: H4 candle closes above the outside-day close by at least 0.05 times H4 ATR(14), closes bullish, body is at least 30% of range, and closes in the upper 40% of the candle.
7. Short follow-through: H4 candle closes below the outside-day close by at least 0.05 times H4 ATR(14), closes bearish, body is at least 30% of range, and closes in the lower 40% of the candle.
8. Frequency control: take at most one setup per outside-day candle.
9. Entry: enter at the first available M5 execution bar at or after the completed H4 signal timestamp, using the existing Phase 0 cost model and one-position-at-a-time rule.
10. Stop: for long setups, stop below the H4 confirmation candle low by 0.25 times H4 ATR(14). For short setups, stop above the H4 confirmation candle high by 0.25 times H4 ATR(14).
11. Target: fixed 1.5R.
12. Invalidation: no setup if D1/H4 indicators are unavailable, the outside day is missing, the H4 confirmation candle quality fails, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is directional continuation after a broad D1 outside bar that closes near its extreme. It should be lower frequency than M5 retest systems and should not require a retest of the broken range. It should lose when the outside-day move exhausts immediately.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- The candidate should provide genuine timeframe diversification only if median hold time exceeds 24 hours and yearly trade count remains below 100.

## Why This Hypothesis Should Exist

A D1 outside day can represent an information shock or forced repricing where both sides of the prior daily range were swept and one side won decisively by the close. If follow-through flows continue during the next H4 cycle, a simple continuation entry may capture the next leg without waiting for a retest.

The hypothesis should only pass if the behavior survives different brokers, cost assumptions, and time windows. If it is only positive in one venue, one side, or one unusually large repricing episode, it should be rejected.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- The candidate only passes through one or two unusually large outside-day episodes.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds breakout-retest, round-number, session-extreme, or discretionary news filters after results are known.

Code mapping after implementation:

- D1 outside-day feature construction: `src/phase0/strategies/d1_outside_day_followthrough_v0.py::D1OutsideDayFollowthroughV0Strategy.prepare_features`
- D1 outside-day state: `src/phase0/strategies/d1_outside_day_followthrough_v0.py::D1OutsideDayFollowthroughV0Strategy._outside_day_at_timestamp`
- H4 follow-through trigger: `src/phase0/strategies/d1_outside_day_followthrough_v0.py::D1OutsideDayFollowthroughV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/d1_outside_day_followthrough_v0.py::D1OutsideDayFollowthroughV0Strategy.build_trade_plan`
