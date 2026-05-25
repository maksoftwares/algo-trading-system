# H4 Credit Spread Stress Momentum v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: corporate credit-spread stress / macro risk momentum
Entry / decision timeframe: H4 completed-candle decision with daily corporate-spread state and M5 execution sequencing
Expected median hold bars M5-equivalent: 72-432
Expected median hold hours: 6-36
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 50-240
Expected cost-adjusted PF: 1.05-1.50
Expected losing-month percentage: 40%-75%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Credit-stress momentum attempts should produce many small failures and fewer 1.65R continuation wins; reject if behavior is one-broker-only, one-credit-cycle-only, or needs post-result threshold edits.

## Mechanical Definition

This candidate is a research-only corporate credit-spread stress hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG relative-value, FX proxy, real-yield/dollar proxy, breakeven-inflation, Treasury curve, COT positioning, GVZ, VIX, financial-conditions NFCI/ANFCI, price-only volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H4 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. External credit-spread source: FRED `BAA10Y` and `AAA10Y`.
4. No-lookahead rule: daily credit-spread features are shifted by one observation before they are merged into H4 bars. An H4 decision can only use prior published credit observations.
5. Credit features:
   - daily Moody's Baa corporate yield spread versus 10-year Treasury
   - daily Moody's Aaa corporate yield spread versus 10-year Treasury
   - daily Baa minus Aaa quality spread
   - 20-business-day change in Baa spread, Aaa spread, and quality spread
   - 252-business-day z-score of the 20-business-day Baa spread change
6. Long credit-stress state: shifted Baa spread 20-day change is at least +0.14 percentage points and shifted quality-spread 20-day change is at least +0.04 percentage points, or shifted Baa spread change z-score is at least +0.65.
7. Long H4 confirmation: H4 close is above EMA40, the completed H4 candle is bullish, and 6-H4 log return is positive.
8. Short credit-relief state: shifted Baa spread 20-day change is at most -0.14 percentage points and shifted quality-spread 20-day change is at most -0.04 percentage points, or shifted Baa spread change z-score is at most -0.65.
9. Short H4 confirmation: H4 close is below EMA40, the completed H4 candle is bearish, and 6-H4 log return is negative.
10. Frequency control: at most one signal per UTC day and direction.
11. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
12. Stop: 1.20 H4 ATR14 from the estimated entry price.
13. Target: fixed 1.65R target.
14. Time stop: 432 M5 bars, matching a 36-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if corporate credit stress adds information beyond spot-gold price structure, VIX, NFCI/ANFCI, real yields, breakevens, and Treasury curve shocks. It should fail if strength only appears in one broker window, one crisis episode, or same-family H4 price momentum alone.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked credit-spread state plus H4 momentum confirmation.

## Why This Hypothesis Should Exist

The search has tested spot-gold structure, intermarket XAG/FX, learned-state, real-yield/dollar macro, breakeven inflation, futures positioning, options-implied volatility, equity-risk implied volatility, broad financial conditions, and nominal Treasury curve stress without finding an independent EA. Corporate credit spreads isolate default/liquidity stress in private credit markets and can affect gold differently from equity volatility or broad financial-condition aggregates.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one credit cycle, or one calendar window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the credit-spread thresholds, H4 confirmation, stop size, target, or frequency rule after seeing this v0 result.
