# W1 D1 Momentum Continuation v0 Hypothesis

Hypothesis date: 2026-05-24
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: W1/D1 directional momentum continuation
Entry / decision timeframe: D1 signal timestamp with W1-scale 20-day momentum state, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 288-1440
Expected median hold hours: 24-120
Expected decisions per week: 0-1
Timeframe diversification qualifies: yes
Expected trade count per year: 15-80
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-70%
Expected worst single month: -8R to -25R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Weekly/daily continuation losses near -1R, fewer +1.5R winners, and no acceptable pass if one yearly trend dominates the result.

## Mechanical Definition

This candidate is a bidirectional XAUUSD W1/D1 momentum-continuation expert using D1 bars only for decision timing. It is not a breakout-retest, fixed-level reclaim, sweep-retest, round-number, session-extreme, VWAP, or intraday trigger strategy. It tests whether broad 20-day directional pressure plus a completed D1 continuation candle has edge after realistic costs.

The mechanical setup is:

1. Market and decision timeframe: XAUUSD with W1-scale 20-day D1 momentum state and D1 completed-candle decisions. M5 bars are used only by the existing simulator for market-entry and exit sequencing.
2. Long state: latest completed D1 close has 20-day close momentum at least 1.25 times D1 ATR(14), five-day close momentum at least 0.25 times D1 ATR(14), close above open, daily body at least 35% of daily range, daily range at least 75% of D1 ATR(14), and close in the upper 35% of the daily range.
3. Short state: latest completed D1 close has 20-day close momentum at most -1.25 times D1 ATR(14), five-day close momentum at most -0.25 times D1 ATR(14), close below open, daily body at least 35% of daily range, daily range at least 75% of D1 ATR(14), and close in the lower 35% of the daily range.
4. Frequency control: take at most one setup per ISO week.
5. Entry: enter at the first available M5 execution bar at or after the completed D1 signal timestamp, using the existing Phase 0 cost model and one-position-at-a-time rule.
6. Stop: for long setups, place the stop below the D1 signal candle low by 0.20 times D1 ATR(14). For short setups, place the stop above the D1 signal candle high by 0.20 times D1 ATR(14).
7. Target: use a fixed 1.5R target.
8. Invalidation: no setup if D1 indicators are unavailable, momentum state is not active, signal candle quality fails, that ISO week has already produced a setup, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is slower and less cost-sensitive than intraday systems. It should capture continuation in strong multi-week gold moves and lose during late-stage trend reversals or range chop. It should not require intraday levels or retests to work.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- The edge should be less cost-sensitive than M5 retest variants because decision frequency and expected hold time are slower.

## Why This Hypothesis Should Exist

Gold can trend across multiple weeks when macro repricing, positioning, and liquidity flows align. A broad 20-day momentum state plus a completed D1 continuation candle is a simple way to test whether those flows persist beyond a single session. A pass would add a slower, non-level behavior family to the candidate bench.

This hypothesis should only pass if W1/D1 momentum continuation survives across brokers, cost models, and time windows. If it only works in one long gold trend, it should be rejected.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- The candidate only passes through one unusually strong yearly trend.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds discretionary news, level, retest, session, or symbol filters after results are known.

Code mapping after implementation:

- D1 feature construction: `src/phase0/strategies/w1_d1_momentum_continuation_v0.py::W1D1MomentumContinuationV0Strategy.prepare_features`
- D1 signal/state classification: `src/phase0/strategies/w1_d1_momentum_continuation_v0.py::W1D1MomentumContinuationV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/w1_d1_momentum_continuation_v0.py::W1D1MomentumContinuationV0Strategy.build_trade_plan`
