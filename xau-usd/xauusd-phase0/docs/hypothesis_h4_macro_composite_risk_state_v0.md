# H4 Macro Composite Risk State v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: fixed macro composite / AI-style risk-state vote
Entry / decision timeframe: H4 completed-candle decision with shifted daily/weekly macro state and M5 execution sequencing
Expected median hold bars M5-equivalent: 72-432
Expected median hold hours: 6-36
Expected decisions per week: 0-6
Timeframe diversification qualifies: yes
Expected trade count per year: 30-180
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 40%-80%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Composite macro-state attempts should be selective and may have sparse months; reject if behavior is one-broker-only, one-crisis-only, or needs post-result threshold edits.

## Mechanical Definition

This candidate is a research-only fixed macro composite. It is not a trained model, not an optimized ensemble, not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG relative-value, FX proxy-only, real-yield-only, breakeven-only, Treasury-curve-only, credit-spread-only, COT positioning, GVZ-only, VIX-only, financial-conditions-only, price-only volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H4 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. External state inputs:
   - FRED `DFII10` and `DTWEXBGS`
   - FRED `T5YIE` and `T10YIE`
   - FRED `DGS2`, `DGS10`, and `T10Y2Y`
   - FRED `BAA10Y` and `AAA10Y`
   - FRED `VIXCLS`
   - FRED `GVZCLS`
   - FRED `NFCI` and `ANFCI`
4. No-lookahead rule: all external macro features are shifted by one observation before they are merged into H4 bars.
5. Every input vote has weight 1. There is no fitting, no learned coefficient, and no threshold selected from outcome data.
6. Bullish votes:
   - 20-business-day real-yield change <= -0.15 percentage points
   - 20-business-day broad-dollar-index change <= -1.00 index points
   - 20-business-day 5-year breakeven change >= +0.10 percentage points
   - 20-business-day 2-year Treasury yield change <= -0.15 percentage points and 10Y-2Y curve-spread change >= +0.03 percentage points
   - 20-business-day Baa credit-spread change >= +0.10 percentage points
   - 20-business-day VIX change >= +3.00 or 20-business-day GVZ change >= +3.00
   - NFCI 4-observation change >= +0.10
7. Bearish votes:
   - 20-business-day real-yield change >= +0.15 percentage points
   - 20-business-day broad-dollar-index change >= +1.00 index points
   - 20-business-day 5-year breakeven change <= -0.10 percentage points
   - 20-business-day 2-year Treasury yield change >= +0.15 percentage points and 10Y-2Y curve-spread change <= -0.03 percentage points
   - 20-business-day Baa credit-spread change <= -0.10 percentage points
   - 20-business-day VIX change <= -3.00 or 20-business-day GVZ change <= -3.00
   - NFCI 4-observation change <= -0.10
8. Composite score: bullish vote count minus bearish vote count.
9. Long macro state: composite score >= +3.
10. Short macro state: composite score <= -3.
11. Long H4 confirmation: H4 close is above EMA40, the completed H4 candle is bullish, and 6-H4 log return is positive.
12. Short H4 confirmation: H4 close is below EMA40, the completed H4 candle is bearish, and 6-H4 log return is negative.
13. Frequency control: at most one signal per UTC day and direction.
14. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
15. Stop: 1.20 H4 ATR14 from the estimated entry price.
16. Target: fixed 1.65R target.
17. Time stop: 432 M5 bars, matching a 36-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if a fixed cross-domain macro vote produces information beyond any single rejected macro lane. It should fail if the composite merely recreates one input family, becomes one-crisis-only, or cannot survive all three broker windows after costs.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell unless the selectivity itself proves too sparse.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked vote table plus H4 momentum confirmation.

## Why This Hypothesis Should Exist

The owner asked whether AI-style thinking can be integrated into the search. This v0 does that in a controlled way: it uses a transparent, fixed macro voting table rather than model fitting, genetic search, or post-result tuning. The goal is to test whether several weak independent macro families become useful only when they agree.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one crisis, one calendar window, or one input family.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the vote table, composite threshold, H4 confirmation, stop size, target, or frequency rule after seeing this v0 result.
