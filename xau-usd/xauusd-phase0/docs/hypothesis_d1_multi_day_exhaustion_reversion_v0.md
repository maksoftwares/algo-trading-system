# D1 Multi-Day Exhaustion Reversion v0 Hypothesis

Hypothesis date: 2026-05-24
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: D1 multi-day exhaustion with H4 reversal confirmation
Entry / decision timeframe: D1 state and H4 signal timestamp, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 288-1152
Expected median hold hours: 24-96
Expected decisions per week: 0-2
Timeframe diversification qualifies: yes
Expected trade count per year: 20-100
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -24R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Sparse counter-move losses near -1R, fewer +1.75R winners, and no acceptable pass if one exhaustion episode dominates the result.

## Mechanical Definition

This candidate is a bidirectional XAUUSD D1 multi-day exhaustion and H4 reversal expert. It is not a breakout-retest, fixed-level reclaim, sweep-retest, round-number, session-extreme, VWAP, or M5 trigger strategy. It tests whether a five-day directional extension that becomes stretched versus D1 ATR has enough mean-reversion pressure to justify an H4 reversal entry.

The mechanical setup is:

1. Market and decision timeframe: XAUUSD with D1 extension state and H4 completed-candle decisions. M5 bars are used only by the existing simulator for market-entry and exit sequencing.
2. Upside D1 exhaustion: latest completed D1 close has five-day close momentum at least 1.75 times D1 ATR(14), at least four of the last five daily closes were up closes, and the latest close is in the upper 15% of the five-day high-low range.
3. Downside D1 exhaustion: latest completed D1 close has five-day close momentum at most -1.75 times D1 ATR(14), at least four of the last five daily closes were down closes, and the latest close is in the lower 15% of the five-day high-low range.
4. Active window: after a qualifying D1 extension closes, search only the first 72 hours of completed H4 bars after that D1 close.
5. Short reversal confirmation: after upside exhaustion, a completed H4 candle must close bearish, have body at least 25% of its range, close in the lower 35% of its range, and have upper wick at least 15% of its range.
6. Long reversal confirmation: after downside exhaustion, a completed H4 candle must close bullish, have body at least 25% of its range, close in the upper 35% of its range, and have lower wick at least 15% of its range.
7. Frequency control: take at most one setup per D1 extension candle and direction.
8. Entry: enter at the first available M5 execution bar at or after the completed H4 signal timestamp, using the existing Phase 0 cost model and one-position-at-a-time rule.
9. Stop: for long setups, place the stop below the H4 reversal candle low by 0.30 times H4 ATR(14). For short setups, place the stop above the H4 reversal candle high by 0.30 times H4 ATR(14).
10. Target: use a fixed 1.75R target.
11. Invalidation: no setup if D1/H4 indicators are unavailable, D1 extension state is not active, H4 reversal candle quality fails, the extension has already been used, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is low frequency and slower holding period than intraday retest systems. It should catch partial normalization after a stretched five-day gold move, especially when H4 candles show rejection rather than continuation. It should lose when a directional repricing trend persists for several more days.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- The edge should be less cost-sensitive than M5 retest variants because decision frequency and expected hold time are slower.

## Why This Hypothesis Should Exist

Gold can overshoot across several sessions when macro repricing and momentum flows move in the same direction. After a five-day extension, liquidity providers and shorter-horizon participants may fade the move when H4 candles begin rejecting the stretched direction. This candidate tests a non-level exhaustion behavior rather than another continuation-after-retest mechanism.

This hypothesis should only pass if the reversal behavior survives across brokers, cost assumptions, and time windows. If it depends on a single crisis period, one venue, or one unusually large reversal episode, it should be rejected.

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
- Any future improvement adds discretionary news, level, retest, session, or symbol filters after results are known.

Code mapping after implementation:

- D1 extension feature construction: `src/phase0/strategies/d1_multi_day_exhaustion_reversion_v0.py::D1MultiDayExhaustionReversionV0Strategy.prepare_features`
- D1 extension-state classification: `src/phase0/strategies/d1_multi_day_exhaustion_reversion_v0.py::D1MultiDayExhaustionReversionV0Strategy._d1_extension_at_timestamp`
- H4 reversal trigger: `src/phase0/strategies/d1_multi_day_exhaustion_reversion_v0.py::D1MultiDayExhaustionReversionV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/d1_multi_day_exhaustion_reversion_v0.py::D1MultiDayExhaustionReversionV0Strategy.build_trade_plan`
