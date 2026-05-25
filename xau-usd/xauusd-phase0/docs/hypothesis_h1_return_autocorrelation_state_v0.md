# H1 Return Autocorrelation State v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 modeled return-state continuation
Entry / decision timeframe: H1 completed-candle decision, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 144-432
Expected median hold hours: 12-36
Expected decisions per week: 1-5
Timeframe diversification qualifies: yes
Expected trade count per year: 45-180
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many small continuation failures near -1R, fewer +1.5R to +1.8R winners, and rejection if a single volatility regime supplies most of the net profit.

## Mechanical Definition

This candidate is a research-only H1 model-state hypothesis for XAUUSD. It is not a retest, reclaim, round-number, daily/weekly level, session-extreme, VWAP, sweep, inside-day, outside-day, broad-USD proxy, or gold/silver relative-value strategy.

The intended mechanical setup is:

1. Market and decision timeframe: XAUUSD H1 target bars only.
2. Execution timeframe: M5 bars are used only by the existing simulator for market-entry and exit sequencing.
3. Return state: compute completed-bar H1 log returns, rolling 72-hour lag-1 return autocorrelation, 6-hour and 24-hour ATR-normalized momentum, 24-hour directional efficiency, and a 24-hour versus 120-hour realized-volatility ratio.
4. Modeled state: a deterministic score combines persistence, directional efficiency, and volatility stability. This is an auditable modeled-thinking proxy, not a discretionary or external AI call.
5. Long setup: require positive modeled persistence, positive 6-hour and 24-hour momentum, close above the H1 EMA state line, and a bullish completed H1 candle.
6. Short setup: require positive modeled persistence for downside movement, negative 6-hour and 24-hour momentum, close below the H1 EMA state line, and a bearish completed H1 candle.
7. Frequency control: take at most one signal per UTC week and direction.
8. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
9. Stop: ATR-based XAUUSD stop using only completed H1 data.
10. Target: fixed R multiple between 1.5R and 1.8R, selected in the locked implementation before any result-producing run.
11. Invalidation: no setup if lookbacks are incomplete, the volatility ratio is outside the locked stability band, or stop/target construction creates non-positive risk.

## Expected Behavior

Expected behavior is short-horizon continuation when XAUUSD enters a persistent H1 return state. The candidate should not need levels, sessions, cross-symbol data, or shape patterns. It should lose when H1 autocorrelation is not stable, when momentum reverses abruptly, or when the apparent state is only noise.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked return-state score, not by later-added price levels or discretionary filters.

## Why This Hypothesis Should Exist

Many rejected candidates used explicit market geometry: levels, ranges, sweeps, pivots, candles, or cross-market proxies. A rolling return-state model is a different information class. It asks whether XAUUSD has short periods where completed H1 returns persist enough for a simple state machine to harvest continuation.

This is also the safest first step toward AI-style thinking in the research stack. The model produces a transparent score from fixed features, so it can be audited, hash-locked, and falsified before any future machine-learned observer is considered.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one isolated volatility regime or one broker/date window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds retest, fixed-level, round-number, session-extreme, cross-symbol, or discretionary news filters after results are known.
