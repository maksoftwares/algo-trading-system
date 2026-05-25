# H4 Financial Conditions Stress Reversal v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: financial-conditions stress / cross-asset risk reversal
Entry / decision timeframe: H4 completed-candle decision with weekly Chicago Fed financial-conditions state and M5 execution sequencing
Expected median hold bars M5-equivalent: 72-288
Expected median hold hours: 6-24
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 50-220
Expected cost-adjusted PF: 1.05-1.50
Expected losing-month percentage: 40%-75%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Financial-stress reversal attempts should have frequent small failures and fewer 1.55R relief wins; reject if the behavior only works in one stress episode, one broker, or after post-result threshold edits.

## Mechanical Definition

This candidate is a research-only financial-conditions hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG relative-value, FX proxy, real-yield proxy, COT positioning, gold-options GVZ implied volatility, equity-options VIX implied volatility, price-only volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H4 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. External financial-conditions source: FRED `NFCI` and `ANFCI`, the Chicago Fed National Financial Conditions Index and adjusted index.
4. No-lookahead rule: weekly NFCI/ANFCI observations are shifted by one observation before they are merged into H4 bars. An H4 decision can only use previously published weekly observations.
5. Financial-conditions features:
   - weekly NFCI value
   - weekly ANFCI value
   - 8-week NFCI change
   - 8-week ANFCI change
   - 156-week rolling percentile of NFCI
6. Long tightening/stress state: shifted NFCI percentile is at or above 0.65, or shifted 8-week NFCI change is at least 0.20, or shifted 8-week ANFCI change is at least 0.15.
7. Long H4 confirmation: 12-H4 log return is at or below -0.003, the completed H4 candle is bullish, the close is in the upper 45% of the candle range, and the close is not more than 0.75 H4 ATR14 below EMA40.
8. Short easing/relief state: shifted NFCI percentile is at or below 0.40 and shifted 8-week NFCI change is at or below -0.10, or shifted 8-week ANFCI change is at or below -0.10.
9. Short H4 confirmation: 12-H4 log return is at or above 0.003, the completed H4 candle is bearish, the close is in the lower 45% of the candle range, and the close is not more than 0.75 H4 ATR14 above EMA40.
10. Frequency control: at most one signal per UTC day and direction.
11. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
12. Stop: 1.15 H4 ATR14 from the estimated entry price.
13. Target: fixed 1.55R target.
14. Time stop: 288 M5 bars, matching a 24-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if broad U.S. financial-conditions stress adds information beyond spot-gold price structure and survives across Capital.com, Pepperstone, and Dukascopy windows after costs. It should fail if the weekly series is too slow, one-crisis-only, or merely duplicates risk/volatility already visible in gold bars.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked financial-conditions state plus H4 reversal confirmation.

## Why This Hypothesis Should Exist

The search has exhausted XAU-only structure, intermarket XAG/FX, learned-state, real-yield macro, futures-positioning COT, gold-options GVZ, and equity-risk VIX lanes without finding an independent EA. NFCI/ANFCI is a separate information class: a broad weekly measure of financial conditions across money markets, debt/equity markets, and banking systems.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one financial-stress episode, or one calendar window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the financial-conditions thresholds, H4 reversal rule, stop size, target, or frequency rule after seeing this v0 result.
