# D1 Compression H4 Expansion v0 Hypothesis

Hypothesis date: 2026-05-24
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: D1 volatility compression with H4 expansion continuation
Entry / decision timeframe: D1 state and H4 signal timestamp, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 288-1152
Expected median hold hours: 24-96
Expected decisions per week: 0-2
Timeframe diversification qualifies: yes
Expected trade count per year: 20-100
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -22R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Sparse continuation losses near -1R, fewer +1.75R winners, and no acceptable pass if one compression cluster dominates the result.

## Mechanical Definition

This candidate is a bidirectional XAUUSD D1 compression and H4 expansion-continuation expert. It is not a breakout-retest, fixed-level reclaim, sweep-retest, round-number, session-extreme, VWAP, or M5 trigger strategy. It tests whether a completed H4 expansion candle that appears after a compressed daily volatility regime has continuation value over a multi-session holding window.

The mechanical setup is:

1. Market and decision timeframe: XAUUSD with D1 compression state and H4 completed-candle decisions. M5 bars are used only by the existing simulator for market-entry and exit sequencing.
2. D1 compression state: latest completed D1 bar must have a rolling 5-day high-low width at or below 85% of the prior 20-day median of that same 5-day width.
3. D1 volatility state: latest completed D1 ATR(14) must be no more than 105% of the prior 20-day median D1 ATR(14).
4. Long H4 expansion trigger: completed H4 candle range must be at least 1.35 times H4 ATR(14), body must be at least 55% of candle range, close must be above open, and close must be in the upper 25% of the candle range.
5. Short H4 expansion trigger: completed H4 candle range must be at least 1.35 times H4 ATR(14), body must be at least 55% of candle range, close must be below open, and close must be in the lower 25% of the candle range.
6. Frequency control: take at most one setup per completed D1 compression bar and direction.
7. Entry: enter at the first available M5 execution bar at or after the completed H4 signal timestamp, using the existing Phase 0 cost model and one-position-at-a-time rule.
8. Stop: for long setups, place the stop below the H4 expansion candle low by 0.25 times H4 ATR(14). For short setups, place the stop above the H4 expansion candle high by 0.25 times H4 ATR(14).
9. Target: use a fixed 1.75R target.
10. Invalidation: no setup if D1/H4 indicators are unavailable, D1 compression state is not active, H4 expansion candle quality fails, the same compression bar and direction has already been used, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is low frequency and slower holding period than intraday retest systems. It should capture directional release after multi-day volatility compression without depending on fixed price levels, retests, sweeps, or session structures. It should lose when the H4 expansion is a one-bar exhaustion move or when daily compression resolves into chop rather than continuation.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- The edge should be less cost-sensitive than M5 retest variants because decision frequency and expected hold time are slower.

## Why This Hypothesis Should Exist

Gold often transitions from multi-day range compression into directional repricing when macro expectations, liquidity, and positioning are forced to adjust after a quiet period. A completed H4 expansion candle can represent the first observable directional release from that compressed daily state. This candidate intentionally avoids all retest and level mechanics so that a pass would improve behavioral diversification rather than adding another timeframe flavor of the existing breakout-retest family.

This hypothesis should show a real edge only if daily compression followed by H4 directional expansion captures a persistent volatility-release behavior after realistic costs. If it only works on one venue, one time slice, or a small number of unusually large trades, it should be rejected.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- The candidate only passes through one or two compression-release episodes.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds discretionary news, level, retest, session, or symbol filters after results are known.

Code mapping after implementation:

- D1 compression feature construction: `src/phase0/strategies/d1_compression_h4_expansion_v0.py::D1CompressionH4ExpansionV0Strategy.prepare_features`
- D1 compression-state classification: `src/phase0/strategies/d1_compression_h4_expansion_v0.py::D1CompressionH4ExpansionV0Strategy._d1_compression_at_timestamp`
- H4 expansion trigger: `src/phase0/strategies/d1_compression_h4_expansion_v0.py::D1CompressionH4ExpansionV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/d1_compression_h4_expansion_v0.py::D1CompressionH4ExpansionV0Strategy.build_trade_plan`
