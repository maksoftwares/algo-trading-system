# H4 Inside Bar D1 Momentum Breakout v0 Hypothesis

Hypothesis date: 2026-05-24
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 inside-bar breakout with D1 momentum gating
Entry / decision timeframe: D1 state and H4 signal timestamp, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 144-864
Expected median hold hours: 12-72
Expected decisions per week: 0-2
Timeframe diversification qualifies: partial
Expected trade count per year: 20-120
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-70%
Expected worst single month: -8R to -24R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Breakout losses near -1R, fewer +1.5R winners, and no acceptable pass if one venue or year dominates the result.

## Mechanical Definition

This candidate is a bidirectional XAUUSD H4 inside-bar breakout expert gated by D1 momentum. It is not a breakout-retest, fixed external level, sweep-retest, round-number, session-extreme, VWAP, or M5 trigger strategy. It tests whether a completed H4 breakout from an inside-bar structure has continuation value when the five-day D1 direction agrees.

The mechanical setup is:

1. Market and decision timeframe: XAUUSD with D1 momentum state and H4 completed-candle decisions. M5 bars are used only by the existing simulator for market-entry and exit sequencing.
2. H4 inside bar: a completed H4 candle must have high no greater than the prior H4 mother candle high, low no lower than the mother candle low, range no more than 70% of mother candle range, and mother candle range at least 60% of prior H4 ATR(14).
3. Long D1 state: latest completed D1 close has five-day close momentum at least 0.50 times D1 ATR(14), and at least three of the last five daily closes were up closes.
4. Short D1 state: latest completed D1 close has five-day close momentum at most -0.50 times D1 ATR(14), and at least three of the last five daily closes were down closes.
5. Long H4 breakout: within three completed H4 bars after the inside bar, a completed H4 candle must close at least 0.05 H4 ATR(14) above the mother candle high, close above open, have body at least 35% of candle range, and close in the upper 35% of its range.
6. Short H4 breakout: within three completed H4 bars after the inside bar, a completed H4 candle must close at least 0.05 H4 ATR(14) below the mother candle low, close below open, have body at least 35% of candle range, and close in the lower 35% of its range.
7. Frequency control: take at most one setup per inside bar and direction.
8. Entry: enter at the first available M5 execution bar at or after the completed H4 breakout timestamp, using the existing Phase 0 cost model and one-position-at-a-time rule.
9. Stop: for long setups, stop at the inside-bar low or 0.75 H4 ATR below entry, whichever is farther. For short setups, stop at the inside-bar high or 0.75 H4 ATR above entry, whichever is farther.
10. Target: use a fixed 1.5R target.
11. Invalidation: no setup if D1/H4 indicators are unavailable, D1 momentum state is not active, inside-bar quality fails, breakout candle quality fails, the inside bar and direction has already been used, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is lower frequency than M5/M15 retest systems and more direct than pullback systems. It should capture continuation from H4 contraction structures when D1 direction agrees. It should lose during false breaks, late trend exhaustion, and range-bound volatility.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- The edge should be less cost-sensitive than M5 retest variants because decision frequency and expected hold time are slower.

## Why This Hypothesis Should Exist

Gold frequently compresses inside a prior H4 candle before repricing when higher-timeframe momentum is already aligned. The inside-bar structure gives an objective contraction/expansion setup without relying on fixed external levels or a retest. A pass would add a slower breakout-continuation behavior that is not merely another M5 retest of an already broken level.

This hypothesis should only pass if H4 inside-bar breakouts survive across brokers, cost models, and time windows. If it only works on one venue or a few outlier weeks, it should be rejected.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- The candidate only passes through one or two unusually large breakout periods.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds discretionary news, retest, session, or symbol filters after results are known.

Code mapping after implementation:

- D1/H4 feature construction: `src/phase0/strategies/h4_inside_bar_d1_momentum_breakout_v0.py::H4InsideBarD1MomentumBreakoutV0Strategy.prepare_features`
- D1 momentum-state classification: `src/phase0/strategies/h4_inside_bar_d1_momentum_breakout_v0.py::H4InsideBarD1MomentumBreakoutV0Strategy._d1_state_at_timestamp`
- H4 inside-bar breakout trigger: `src/phase0/strategies/h4_inside_bar_d1_momentum_breakout_v0.py::H4InsideBarD1MomentumBreakoutV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/h4_inside_bar_d1_momentum_breakout_v0.py::H4InsideBarD1MomentumBreakoutV0Strategy.build_trade_plan`
