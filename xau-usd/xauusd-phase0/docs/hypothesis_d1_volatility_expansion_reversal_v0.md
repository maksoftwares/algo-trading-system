# D1 Volatility Expansion Reversal v0 Hypothesis

Hypothesis date: 2026-05-23
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: D1 volatility expansion exhaustion with H4 reversal confirmation
Entry / decision timeframe: D1 state and H4 signal timestamp, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 288-864
Expected median hold hours: 24-72
Expected decisions per week: 0-2
Timeframe diversification qualifies: yes
Expected trade count per year: 20-90
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Sparse reversal losses near -1R, fewer +1.75R winners, and no acceptable pass if one expansion episode dominates the result.

## Mechanical Definition

This candidate is a bidirectional XAUUSD D1 volatility expansion reversal expert. It is not a breakout-retest, level reclaim, sweep-retest, round-number, session-extreme, VWAP, or M5 trigger strategy. It tests whether unusually large completed daily expansion candles often mean-revert or pause enough for an H4 reversal candle to capture a multi-session counter-move.

The mechanical setup is:

1. Market and decision timeframe: XAUUSD with D1 expansion state and H4 completed-candle decisions. M5 bars are used only by the existing simulator for market-entry and exit sequencing.
2. D1 upside expansion: latest completed D1 candle has range at least 1.25 times D1 ATR(14), body at least 55% of the daily range, close in the upper 25% of the daily range, bullish close, and three-day close momentum at least 0.75 times D1 ATR(14).
3. D1 downside expansion: latest completed D1 candle has range at least 1.25 times D1 ATR(14), body at least 55% of the daily range, close in the lower 25% of the daily range, bearish close, and three-day close momentum at most -0.75 times D1 ATR(14).
4. Active window: after a qualifying D1 expansion closes, search only the first 24 hours of completed H4 bars after that D1 close.
5. Short reversal confirmation: after D1 upside expansion, a completed H4 candle must close bearish, have body at least 25% of its range, close in the lower 35% of its range, and have upper wick at least 20% of its range.
6. Long reversal confirmation: after D1 downside expansion, a completed H4 candle must close bullish, have body at least 25% of its range, close in the upper 35% of its range, and have lower wick at least 20% of its range.
7. Frequency control: take at most one setup per D1 expansion candle and direction.
8. Entry: enter at the first available M5 execution bar at or after the completed H4 signal timestamp, using the existing Phase 0 cost model and one-position-at-a-time rule.
9. Stop: for long setups, place the stop below the H4 reversal candle low by 0.30 times H4 ATR(14). For short setups, place the stop above the H4 reversal candle high by 0.30 times H4 ATR(14).
10. Target: use a fixed 1.75R target.
11. Invalidation: no setup if D1/H4 indicators are unavailable, D1 expansion state is not active, H4 reversal candle quality fails, the expansion has already been used, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is low frequency and slower holding period than intraday retest systems. It should catch exhaustion after unusually large daily expansions, especially when the next H4 candle shows rejection rather than continuation. It should lose when the daily expansion begins a genuine multi-day repricing trend.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- The edge should be less cost-sensitive than M5 retest variants because decision frequency and expected hold time are slower.

## Why This Hypothesis Should Exist

Gold can overshoot after large daily volatility expansions as forced buying/selling, option hedging, and momentum flows exhaust near the end of a session. A confirmed H4 reversal in the first day after that expansion may capture normalization without requiring any fixed price level or breakout-retest premise.

This candidate directly tests a non-level behavior family after the first H4/D1 momentum-pullback attempt failed. It should not be counted as same-family with `breakout_retest` because the edge thesis is exhaustion after daily volatility expansion, not continuation after a broken level retests.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- The candidate only passes through one or two unusually large reversal episodes.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds discretionary time, news, level, volatility, or candle filters after results are known.

Code mapping after implementation:

- D1 expansion feature construction: `src/phase0/strategies/d1_volatility_expansion_reversal_v0.py::D1VolatilityExpansionReversalV0Strategy.prepare_features`
- D1 expansion-state classification: `src/phase0/strategies/d1_volatility_expansion_reversal_v0.py::D1VolatilityExpansionReversalV0Strategy._d1_expansion_at_timestamp`
- H4 reversal trigger: `src/phase0/strategies/d1_volatility_expansion_reversal_v0.py::D1VolatilityExpansionReversalV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/d1_volatility_expansion_reversal_v0.py::D1VolatilityExpansionReversalV0Strategy.build_trade_plan`
