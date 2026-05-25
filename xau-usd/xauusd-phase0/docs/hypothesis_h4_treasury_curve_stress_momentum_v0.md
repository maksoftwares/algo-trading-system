# H4 Treasury Curve Stress Momentum v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: nominal Treasury-rate and yield-curve stress / macro momentum
Entry / decision timeframe: H4 completed-candle decision with daily Treasury curve state and M5 execution sequencing
Expected median hold bars M5-equivalent: 72-432
Expected median hold hours: 6-36
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 50-240
Expected cost-adjusted PF: 1.05-1.50
Expected losing-month percentage: 40%-75%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Nominal-rate shock attempts should produce many small failures and fewer 1.65R continuation wins; reject if behavior is one-broker-only, one-rate-cycle-only, or needs post-result threshold edits.

## Mechanical Definition

This candidate is a research-only nominal Treasury-rate and curve-stress hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG relative-value, FX proxy, real-yield/dollar proxy, breakeven-inflation, COT positioning, GVZ, VIX, financial-conditions NFCI/ANFCI, price-only volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H4 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. External Treasury source: FRED `DGS2`, `DGS10`, and `T10Y2Y`.
4. No-lookahead rule: daily Treasury features are shifted by one observation before they are merged into H4 bars. An H4 decision can only use prior published Treasury observations.
5. Treasury features:
   - daily 2-year Treasury constant maturity yield
   - daily 10-year Treasury constant maturity yield
   - daily 10-year minus 2-year Treasury spread
   - 20-business-day change in 2-year yield, 10-year yield, and curve spread
   - 252-business-day z-score of the 20-business-day 2-year yield change
6. Long easing/steepening state: shifted 2-year yield 20-day change is at most -0.18 percentage points, shifted 10-year yield 20-day change is at most -0.12 percentage points, and either the shifted curve-spread 20-day change is at least +0.05 percentage points or the shifted 2-year change z-score is at most -0.65.
7. Long H4 confirmation: H4 close is above EMA40, the completed H4 candle is bullish, and 6-H4 log return is positive.
8. Short tightening/flattening state: shifted 2-year yield 20-day change is at least +0.18 percentage points, shifted 10-year yield 20-day change is at least +0.12 percentage points, and either the shifted curve-spread 20-day change is at most -0.05 percentage points or the shifted 2-year change z-score is at least +0.65.
9. Short H4 confirmation: H4 close is below EMA40, the completed H4 candle is bearish, and 6-H4 log return is negative.
10. Frequency control: at most one signal per UTC day and direction.
11. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
12. Stop: 1.20 H4 ATR14 from the estimated entry price.
13. Target: fixed 1.65R target.
14. Time stop: 432 M5 bars, matching a 36-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if nominal Treasury-rate and curve shocks add information beyond spot-gold price structure, real yields, breakevens, and broad financial conditions. It should fail if all strength comes from one broker window, one 2020-2022 rate-cycle episode, or same-family price momentum alone.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked Treasury curve state plus H4 momentum confirmation.

## Why This Hypothesis Should Exist

The search has tested spot-gold structure, intermarket XAG/FX, learned-state, real-yield/dollar macro, breakeven inflation, futures positioning, options-implied volatility, equity-risk implied volatility, and broad financial conditions without finding an independent EA. Nominal Treasury-rate and curve-shape shocks are a separate macro input: gold can react to absolute rate pressure and curve stress even when real-yield or inflation-compensation features do not isolate the same regime.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one rate cycle, or one calendar window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the Treasury thresholds, H4 confirmation, stop size, target, or frequency rule after seeing this v0 result.
