# D1 Momentum H4 Pullback v0 Hypothesis

Hypothesis date: 2026-05-23
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: D1 directional momentum with H4 trend pullback continuation
Entry / decision timeframe: H4 decision and H4 signal timestamp, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 288-864
Expected median hold hours: 24-72
Expected decisions per week: 0-2
Timeframe diversification qualifies: yes
Expected trade count per year: 25-95
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-65%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Sparse losses near -1R, occasional multi-day 2R winners, and no acceptable pass if a few trend legs dominate total return.

## Mechanical Definition

This candidate is a bidirectional XAUUSD D1 momentum / H4 pullback continuation expert. It is intentionally not a breakout-retest, fixed-level retest, sweep-retest, round-number, session-extreme, VWAP, or M5 trigger strategy. It tests whether broad daily directional momentum persists after a completed H4 pullback into the H4 EMA20 zone.

The mechanical setup is:

1. Market and decision timeframe: XAUUSD, with D1 trend state and H4 completed-candle decisions. M5 bars are used only by the existing simulator for market-entry and exit sequencing.
2. D1 long state: latest completed D1 close is above D1 EMA20, D1 EMA20 is above D1 EMA50, D1 EMA20 slope over five D1 bars is positive, and five-day close momentum is at least 0.25 times current D1 ATR(14).
3. D1 short state: latest completed D1 close is below D1 EMA20, D1 EMA20 is below D1 EMA50, D1 EMA20 slope over five D1 bars is negative, and five-day close momentum is at most -0.25 times current D1 ATR(14).
4. H4 long pullback: while D1 long state is active, a completed H4 candle must trade down into the H4 EMA20 zone, defined as low <= H4 EMA20 + 0.35 times H4 ATR(14), and then close back at or above H4 EMA20 - 0.05 times H4 ATR(14). The candle must close bullish, close above the previous H4 close, and have body at least 20% of its high-low range.
5. H4 short pullback: while D1 short state is active, a completed H4 candle must trade up into the H4 EMA20 zone, defined as high >= H4 EMA20 - 0.35 times H4 ATR(14), and then close back at or below H4 EMA20 + 0.05 times H4 ATR(14). The candle must close bearish, close below the previous H4 close, and have body at least 20% of its high-low range.
6. Frequency control: take at most one setup per ISO week. This keeps the candidate in the intended slower-timeframe lane and avoids turning it into another intraday cost-sensitive variant.
7. Entry: enter at the first available M5 execution bar at or after the completed H4 signal timestamp, using the existing Phase 0 cost model and one-position-at-a-time rule.
8. Stop: for long setups, place the stop below the H4 pullback candle low by 0.25 times H4 ATR(14). For short setups, place the stop above the H4 pullback candle high by 0.25 times H4 ATR(14).
9. Target: use a fixed 2.0R target.
10. Invalidation: no setup if D1 or H4 indicators are unavailable, D1 momentum state is not active, H4 candle quality fails, the weekly frequency slot is already used, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is low frequency and slower holding period than the accepted breakout-retest family. It should catch persistent D1 directional legs after H4 pullbacks resume in trend direction. It should lose during daily trend exhaustion, news-driven reversal, and choppy range conditions where H4 pullbacks do not expand.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, despite weekly frequency control.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF, with materially less cost sensitivity than M5 retest variants.
- EURUSD and USDJPY transfer may be weaker than XAUUSD because D1 gold trend persistence can be symbol-specific, but complete non-transfer would require explicit review.

## Why This Hypothesis Should Exist

XAUUSD often trends across multiple sessions when macro direction and positioning align. A daily trend state can persist for days, and H4 pullbacks may offer continuation entries with larger price targets and lower cost-per-R sensitivity than M5 retest systems. This candidate directly tests the Review #5 concern that the research bench lacked true H4/D1 timing and kept finding only intraday level-and-pullback variants.

The expected edge is not that a broken level retests and holds. The expected edge is that daily momentum regimes continue after a completed H4 pullback shows trend-side re-acceptance.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- The candidate only passes through one or two unusually large multi-day winners.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds discretionary time, news, level, volatility, or candle filters after results are known.

Code mapping after implementation:

- D1 momentum feature construction: `src/phase0/strategies/d1_momentum_h4_pullback_v0.py::D1MomentumH4PullbackV0Strategy.prepare_features`
- D1 trend-state classification: `src/phase0/strategies/d1_momentum_h4_pullback_v0.py::D1MomentumH4PullbackV0Strategy._d1_state_at_timestamp`
- H4 pullback trigger: `src/phase0/strategies/d1_momentum_h4_pullback_v0.py::D1MomentumH4PullbackV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/d1_momentum_h4_pullback_v0.py::D1MomentumH4PullbackV0Strategy.build_trade_plan`
