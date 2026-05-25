# H1 Tick Volume Climax Reversal v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 tick-volume participation climax
Entry / decision timeframe: H1 completed-candle decision, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 72-288
Expected median hold hours: 6-24
Expected decisions per week: 1-6
Timeframe diversification qualifies: yes
Expected trade count per year: 50-220
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many failed exhaustion reversals near -1R, fewer +1.4R to +1.6R winners, and rejection if high-volume shock months dominate net profit.

## Mechanical Definition

This candidate is a research-only H1 tick-volume climax hypothesis for XAUUSD. It is not a retest, reclaim, round-number, daily/weekly level, session-extreme, VWAP, sweep, inside-day, outside-day, broad-USD proxy, gold/silver relative-value, H1 autocorrelation-state, or M5 path-skew strategy.

The intended mechanical setup is:

1. Market and decision timeframe: XAUUSD H1 bars only.
2. Execution timeframe: M5 bars are used only by the existing simulator for market-entry and exit sequencing.
3. Participation state: compute completed-bar H1 tick count, rolling prior tick-count z-score, rolling prior tick-count ratio, H1 range in ATR, candle body ratio, and close position.
4. Long setup: require a wide bearish H1 candle with unusually high tick participation and a close that is not pinned to the low, suggesting sell-side climax absorption.
5. Short setup: require a wide bullish H1 candle with unusually high tick participation and a close that is not pinned to the high, suggesting buy-side climax absorption.
6. Frequency control: take at most one signal per UTC day and direction.
7. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
8. Stop: beyond the completed H1 bar extreme plus an ATR buffer.
9. Target: fixed R multiple between 1.4R and 1.6R, selected in the locked implementation before any result-producing run.
10. Invalidation: no setup if tick-count lookbacks are incomplete, ATR is incomplete, H1 range is too small, or stop/target construction creates non-positive risk.

## Expected Behavior

Expected behavior is short-horizon reversal after an H1 bar shows unusually high participation and signs of exhaustion. The candidate should not need price levels, session windows, or cross-symbol data. It should lose when high tick volume simply confirms trend continuation.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked tick-volume climax features, not by later-added price levels or session filters.

## Why This Hypothesis Should Exist

Tick count is a different information source from price-only geometry. A completed H1 bar with unusually high participation may mark forced activity or exhaustion. This hypothesis tests whether participation climax has standalone value when stripped of levels, sessions, and cross-symbol inputs.

The hypothesis should only pass if tick-volume information survives across Capital.com, Pepperstone, and Dukascopy windows. If high participation is only noise or broker-specific, it should fail the matrix.

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
