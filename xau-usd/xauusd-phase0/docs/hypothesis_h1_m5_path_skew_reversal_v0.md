# H1 M5 Path Skew Reversal v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: M5 path-structure proxy inside completed H1 bars
Entry / decision timeframe: H1 completed-candle decision using M5 path features from inside the completed H1 bar
Expected median hold bars M5-equivalent: 72-288
Expected median hold hours: 6-24
Expected decisions per week: 1-8
Timeframe diversification qualifies: yes
Expected trade count per year: 60-260
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many failed reversal attempts near -1R, fewer +1.4R to +1.6R winners, and rejection if profit comes from one isolated shock window.

## Mechanical Definition

This candidate is a research-only H1/M5 path-skew hypothesis for XAUUSD. It is not a retest, reclaim, round-number, daily/weekly level, session-extreme, VWAP, sweep, inside-day, outside-day, broad-USD proxy, gold/silver relative-value, or H1 autocorrelation-state strategy.

The intended mechanical setup is:

1. Market and decision timeframe: XAUUSD H1 bars, but the completed H1 bar is described using the twelve M5 bars inside it.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. Path features: for each completed H1 bar, compute M5 count, first-third M5 return, last-third M5 return, H1 close position, H1 range in ATR, and M5 path efficiency.
4. Long setup: require a wide bearish H1 bar whose early M5 path drove lower but whose last-third M5 path reversed upward enough to suggest late absorption.
5. Short setup: require a wide bullish H1 bar whose early M5 path drove higher but whose last-third M5 path reversed downward enough to suggest late absorption.
6. Frequency control: take at most one signal per UTC day and direction.
7. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
8. Stop: beyond the completed H1 bar extreme plus an ATR buffer.
9. Target: fixed R multiple between 1.3R and 1.6R, selected in the locked implementation before any result-producing run.
10. Invalidation: no setup if the completed H1 bar has fewer than 10 internal M5 bars, incomplete ATR, low range, excessive one-way path efficiency, or non-positive risk.

## Expected Behavior

Expected behavior is short-horizon reversal after an H1 move shows late M5 absorption. The candidate should not need fixed price levels, session windows, or cross-symbol data. It should lose when late path skew is just noisy retracement inside a stronger directional move.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked H1/M5 path features, not by later-added price levels or session filters.

## Why This Hypothesis Should Exist

Most rejected candidates describe where price is relative to external structures or slower indicators. This hypothesis describes how the most recent completed H1 candle was formed internally. It is a lightweight order-flow proxy using only existing bar data and may capture late absorption that a pure H1 close cannot see.

The hypothesis should only pass if path-skew information survives across broker windows and cost assumptions. If it is only a noisy candle-shape variant, it should fail the same matrix gates.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one isolated broker/date window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds retest, fixed-level, round-number, session-extreme, cross-symbol, or discretionary news filters after results are known.
