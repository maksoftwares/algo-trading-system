# H4 Policy Uncertainty Safe Haven v0 Hypothesis

Hypothesis date: 2026-05-26
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: economic policy uncertainty / safe-haven macro momentum
Entry / decision timeframe: H4 completed-candle decision with shifted daily policy-uncertainty state and M5 execution sequencing
Expected median hold bars M5-equivalent: 72-432
Expected median hold hours: 6-36
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 50-260
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 40%-80%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Policy-uncertainty safe-haven attempts should have many small failures and fewer 1.65R continuation wins; reject if behavior is one-broker-only, one-news-cycle-only, or needs post-result threshold edits.

## Mechanical Definition

This candidate is a research-only economic policy uncertainty hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG relative-value, FX proxy, real-yield/dollar proxy, breakeven-inflation, Treasury curve, credit-spread, COT positioning, GVZ, VIX, financial-conditions NFCI/ANFCI, fixed macro-composite vote, price-only volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H4 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. External policy-uncertainty source: FRED `USEPUINDXD`, the daily U.S. economic policy uncertainty index.
4. No-lookahead rule: daily policy-uncertainty features are shifted by one observation before they are merged into H4 bars. An H4 decision can only use prior published observations.
5. Policy-uncertainty features:
   - daily index level
   - 5-business-day mean
   - 120-business-day median
   - 5-day mean divided by the 120-day median
   - 20-business-day change in the daily index
   - 252-business-day z-score of the 20-day change
6. Long safe-haven state: shifted 5-day mean / 120-day median is at least 1.35, or shifted 20-day change z-score is at least +0.75.
7. Long H4 confirmation: H4 close is above EMA40, the completed H4 candle is bullish, and 6-H4 log return is positive.
8. Short calm-state unwind: shifted 5-day mean / 120-day median is at most 0.75 and shifted 20-day change z-score is at most -0.50.
9. Short H4 confirmation: H4 close is below EMA40, the completed H4 candle is bearish, and 6-H4 log return is negative.
10. Frequency control: at most one signal per UTC day and direction.
11. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
12. Stop: 1.20 H4 ATR14 from the estimated entry price.
13. Target: fixed 1.65R target.
14. Time stop: 432 M5 bars, matching a 36-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if policy-uncertainty shocks add information beyond spot-gold price structure, VIX, GVZ, credit spreads, financial conditions, and the macro-composite attempts. It should fail if all strength comes from one broker window, one crisis/news cycle, or H4 price momentum alone.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked policy-uncertainty state plus H4 momentum confirmation.

## Why This Hypothesis Should Exist

The search has tested rates, inflation, credit, volatility, broad financial conditions, and fixed macro voting without finding an approved independent EA. Economic policy uncertainty is a separate newspaper/text-derived public data class that may capture political and fiscal/regulatory shock regimes not fully represented by market-implied volatility or credit/rate measures.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one news cycle, or one calendar window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the policy-uncertainty thresholds, H4 confirmation, stop size, target, or frequency rule after seeing this v0 result.
