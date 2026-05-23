# H4 D1 Momentum Expansion Continuation v0 Hypothesis

Hypothesis date: 2026-05-24
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: D1 directional pressure with H4 expansion continuation
Entry / decision timeframe: D1 state and H4 signal timestamp, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 144-864
Expected median hold hours: 12-72
Expected decisions per week: 0-1
Timeframe diversification qualifies: yes
Expected trade count per year: 20-80
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-70%
Expected worst single month: -8R to -22R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Weekly continuation losses near -1R, fewer +1.5R winners, and no acceptable pass if one directional month dominates the result.

## Mechanical Definition

This candidate is a bidirectional XAUUSD D1 momentum and H4 expansion-continuation expert. It is not a breakout-retest, fixed-level reclaim, sweep-retest, round-number, session-extreme, VWAP, or M5 trigger strategy. It tests whether D1 directional pressure plus a completed H4 expansion candle carries continuation value when entries are throttled to one per ISO week.

The mechanical setup is:

1. Market and decision timeframe: XAUUSD with D1 momentum state and H4 completed-candle decisions. M5 bars are used only by the existing simulator for market-entry and exit sequencing.
2. Long D1 state: latest completed D1 close has five-day close momentum at least 0.75 times D1 ATR(14), and at least three of the last five daily closes were up closes.
3. Short D1 state: latest completed D1 close has five-day close momentum at most -0.75 times D1 ATR(14), and at least three of the last five daily closes were down closes.
4. Long H4 expansion trigger: completed H4 candle range must be at least 1.10 times H4 ATR(14), body must be at least 50% of candle range, close must be above open, close must be in the upper 30% of the candle range, and three-candle H4 close momentum must be at least 0.25 times H4 ATR(14).
5. Short H4 expansion trigger: completed H4 candle range must be at least 1.10 times H4 ATR(14), body must be at least 50% of candle range, close must be below open, close must be in the lower 30% of the candle range, and three-candle H4 close momentum must be at most -0.25 times H4 ATR(14).
6. Frequency control: take at most one setup per ISO week.
7. Entry: enter at the first available M5 execution bar at or after the completed H4 signal timestamp, using the existing Phase 0 cost model and one-position-at-a-time rule.
8. Stop: for long setups, place the stop below the H4 expansion candle low by 0.25 times H4 ATR(14). For short setups, place the stop above the H4 expansion candle high by 0.25 times H4 ATR(14).
9. Target: use a fixed 1.5R target.
10. Invalidation: no setup if D1/H4 indicators are unavailable, D1 momentum state is not active, H4 expansion candle quality fails, that ISO week has already produced a setup, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is lower frequency than M5/M15 retest systems and more frequent than the sparse D1 reversal candidates. It should capture multi-session continuation when D1 pressure and H4 expansion align. It should lose during sharp false momentum bursts and range-bound periods.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- The edge should be less cost-sensitive than M5 retest variants because decision frequency and expected hold time are slower.

## Why This Hypothesis Should Exist

Gold often moves in directional bursts across several H4 bars when daily pressure and intraday expansion agree. This candidate tests that continuation behavior directly, without requiring a prior broken level, retest, sweep, round number, or session reference. A pass would add a higher-timeframe momentum behavior that is mechanically different from the approved breakout-retest family.

This hypothesis should only pass if weekly-throttled H4 expansion continuation is robust across brokers, cost models, and time windows. If it only works on one venue or a few large trend weeks, it should be rejected.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- The candidate only passes through one or two unusually large momentum periods.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds discretionary news, level, retest, session, or symbol filters after results are known.

Code mapping after implementation:

- D1/H4 feature construction: `src/phase0/strategies/h4_d1_momentum_expansion_continuation_v0.py::H4D1MomentumExpansionContinuationV0Strategy.prepare_features`
- D1 momentum-state classification: `src/phase0/strategies/h4_d1_momentum_expansion_continuation_v0.py::H4D1MomentumExpansionContinuationV0Strategy._d1_state_at_timestamp`
- H4 expansion trigger: `src/phase0/strategies/h4_d1_momentum_expansion_continuation_v0.py::H4D1MomentumExpansionContinuationV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/h4_d1_momentum_expansion_continuation_v0.py::H4D1MomentumExpansionContinuationV0Strategy.build_trade_plan`
