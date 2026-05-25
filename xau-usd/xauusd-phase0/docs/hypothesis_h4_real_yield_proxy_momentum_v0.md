# H4 Real Yield Proxy Momentum v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: macro-regime / real-yield and dollar momentum
Entry / decision timeframe: H4 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 144-576
Expected median hold hours: 12-48
Expected decisions per week: 0-6
Timeframe diversification qualifies: yes
Expected trade count per year: 40-250
Expected cost-adjusted PF: 1.05-1.50
Expected losing-month percentage: 40%-75%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Macro-aligned trends should produce fewer but larger 1.80R winners, with rejection if the signal is one-window, one-broker, or crisis-only.

## Mechanical Definition

This candidate is a research-only H4 macro-regime momentum hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG, FX-cross proxy, calendar-drift, volatility-squeeze, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H4 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. External macro source: FRED daily `DFII10` 10-year real-yield observations and FRED daily `DTWEXBGS` broad nominal dollar-index observations.
4. No-lookahead rule: macro features are shifted by one available macro observation before being merged into H4 bars. If a macro observation is not yet available, the candidate uses the latest previously shifted value.
5. Macro features: 20-observation change in `DFII10`, 20-observation log return in `DTWEXBGS`, and rolling 252-observation z-scores for both changes.
6. Long macro state: 20-observation real-yield change is at or below -0.20 percentage points, dollar-index 20-observation return is at or below -0.75%, and at least one of the two macro z-scores is at or below -0.50.
7. Short macro state: 20-observation real-yield change is at or above +0.20 percentage points, dollar-index 20-observation return is at or above +0.75%, and at least one of the two macro z-scores is at or above +0.50.
8. Long H4 confirmation: H4 close is above EMA40, the completed H4 candle is bullish, and 6-H4 log return is positive.
9. Short H4 confirmation: H4 close is below EMA40, the completed H4 candle is bearish, and 6-H4 log return is negative.
10. Frequency control: at most one signal per ISO week and direction.
11. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
12. Stop: 1.20 H4 ATR14 from the estimated entry price.
13. Target: fixed 1.80R target.
14. Time stop: 576 M5 bars, matching a 48-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if macro real-yield and dollar pressure adds information that survives across Capital.com, Pepperstone, and Dukascopy windows after costs. It should fail if the public macro state is too slow, is already absorbed by price, or works only during one gold regime.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked real-yield and dollar-index state plus H4 confirmation.

## Why This Hypothesis Should Exist

The previous `h4_real_yield_proxy_momentum_v0` backlog idea was blocked because no approved real-yield, DXY, Treasury, or macro-proxy series existed locally. This version directly fixes that blocker with public FRED macro data instead of faking macro state from XAU-only bars.

The idea is economically distinct from the approved breakout-retest family: gold should tend to strengthen when real yields and broad dollar pressure fall together, and weaken when both rise together.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one macro shock, or one calendar window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the macro thresholds, H4 confirmation rule, stop size, target, or frequency rule after seeing this v0 result.
