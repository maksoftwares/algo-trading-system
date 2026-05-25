# XAU XAG Relative Value v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: Precious-metals relative-value
Entry / decision timeframe: H1 completed-candle decision, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 144-576
Expected median hold hours: 12-48
Expected decisions per week: 1-6
Timeframe diversification qualifies: yes
Expected trade count per year: 60-220
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many failed relative-value reversions near -1R, fewer +1.5R winners, and rejection if returns are dominated by one metals shock episode.

## Mechanical Definition

This candidate is a blocked H1 research hypothesis for XAUUSD using XAGUSD as a relative-value input. It is not a retest, reclaim, round-number, daily/weekly level, session-extreme, VWAP, sweep, inside-day, outside-day, or broad-USD proxy strategy.

The intended mechanical setup is:

1. Market and decision timeframe: XAUUSD H1 target bars with XAGUSD H1 relative-value context from the same broker and matrix window.
2. Execution timeframe: M5 bars are used only by the existing simulator for market-entry and exit sequencing.
3. Relative spread: compute a rolling log-ratio or beta residual between XAUUSD and XAGUSD using only completed H1 bars.
4. Setup state: require a statistically large XAU/XAG divergence using a rolling z-score, with enough lookback to avoid short-sample behavior.
5. Confirmation: require the completed H1 XAUUSD candle and the relative spread to move in the hypothesized direction without using future bars.
6. Frequency control: take at most one signal per UTC week and direction.
7. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
8. Stop: ATR-based XAUUSD stop using only completed H1 data.
9. Target: fixed R multiple between 1.4R and 1.8R, selected in the locked implementation before any result-producing run.
10. Invalidation: no setup if XAGUSD H1 data is unavailable for the same broker window, if indicator lookbacks are incomplete, or if stop/target construction creates non-positive risk.

Implementation status:

This v0 is intentionally blocked by missing XAGUSD H1 data. No result-producing matrix is authorized until broker-consistent XAGUSD H1 readiness passes and a matching research-only implementation is added.

## Expected Behavior

Expected behavior is short-horizon XAUUSD movement after a meaningful gold/silver relative-value displacement. The candidate should not need price levels, session windows, or sweep/reclaim events. It should lose when the XAU/XAG spread continues trending or when silver-specific movement has no predictive value for gold.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must survive broker-consistent XAGUSD inputs; substituting another broker's XAGUSD data invalidates the result.

## Why This Hypothesis Should Exist

Gold and silver share precious-metals flows but differ in industrial sensitivity, liquidity, and volatility. A relative-value signal may capture metals-specific pressure that is not visible in XAUUSD alone and is distinct from broad USD proxy behavior. This creates a genuinely different information class from the rejected XAU-only and FX-proxy candidates.

The hypothesis should only pass if the relative-value relationship survives across broker windows and cost assumptions. If strength appears only in one venue, one year, or one metals shock, it should be rejected.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Required XAGUSD H1 broker-consistent data cannot be acquired.
- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one isolated metals shock or one broker/date window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds retest, fixed-level, round-number, session-extreme, or discretionary news filters after results are known.
