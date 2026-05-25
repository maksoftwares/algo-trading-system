# H1 Volatility Squeeze Breakout v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: volatility-compression expansion
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 36-144
Expected median hold hours: 3-12
Expected decisions per week: 2-20
Timeframe diversification qualifies: yes
Expected trade count per year: 100-700
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-70%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many failed expansion attempts, fewer +1.60R winners, and rejection if compression breakouts only work in one broker/date window.

## Mechanical Definition

This candidate is a research-only H1 volatility squeeze breakout hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, intermarket proxy, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H1 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. Compression measure: 20-H1 Bollinger width normalized by H1 ATR14.
4. Compression rank: the current normalized width percentile over the prior 240 completed H1 bars, using only information available before the signal bar.
5. Expansion trigger: the signal H1 candle closes outside its 20-H1 Bollinger band after prior compression.
6. Long setup: prior compression percentile is at or below 0.25, the completed H1 candle closes above the upper band, the candle is bullish, body ratio is at least 0.45, close position is at least 0.70, and price is above EMA50.
7. Short setup: prior compression percentile is at or below 0.25, the completed H1 candle closes below the lower band, the candle is bearish, body ratio is at least 0.45, close position is at most 0.30, and price is below EMA50.
8. Frequency control: at most one signal per UTC day and direction.
9. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
10. Stop: signal candle extreme plus 0.25 H1 ATR buffer.
11. Target: fixed 1.60R target.
12. Time stop: 144 M5 bars, matching a 12-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if H1 compression followed by decisive expansion has cross-venue persistence after costs. It should fail if squeeze breakouts are just another high-turnover noise pattern or only survive in one data vendor/window.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked Bollinger-width compression and expansion rule.

## Why This Hypothesis Should Exist

The project has rejected many level/retest, intermarket, learned-state, and higher-timeframe momentum attempts. This lane tests a different middle-timeframe behavior: whether realized volatility compression creates enough post-break expansion to survive costs.

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
- Any future improvement changes the Bollinger window, compression threshold, stop size, target, or frequency rule after seeing this v0 result.
