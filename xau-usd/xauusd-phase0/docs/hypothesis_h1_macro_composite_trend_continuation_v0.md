# H1 Macro Composite Trend Continuation v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: macro-composite / trend-continuation timing
Entry / decision timeframe: H1 completed-candle decision with shifted public daily/weekly macro state and M5 execution sequencing
Expected median hold bars M5-equivalent: 48-144
Expected median hold hours: 4-12
Expected decisions per week: 2-15
Timeframe diversification qualifies: yes
Expected trade count per year: 150-1200
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-75%
Expected worst single month: -8R to -24R
Expected max consecutive zero months: 2
Expected R-multiple distribution: macro state should bias trend direction, while H1 trend-continuation candles provide frequent enough timing; reject if evidence is one-broker, one-window, or concentration-led.

## Mechanical Definition

This candidate is a research-only fixed macro-composite trend-continuation hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG, GLD-flow, COT, futures-volume, volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H1 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. Macro sources: the existing public macro-composite inputs already used by the Phase 0 package: real yield and broad dollar index, breakeven inflation, Treasury curve, credit spread, VIX, GVZ, and financial-conditions frames.
4. No-lookahead rule: macro vote features are shifted by one macro observation before merging into H1 bars.
5. Bull macro votes use the existing fixed definitions from `h4_macro_composite_risk_state_v0`: falling real yields, falling broad dollar, rising 5y breakeven inflation, falling 2y rates plus steepening curve, widening BAA spread, rising VIX/GVZ, and rising NFCI.
6. Bear macro votes use the symmetric existing fixed definitions.
7. Long macro state: composite score is at least +2 and bull votes are at least 3.
8. Short macro state: composite score is at most -2 and bear votes are at least 3.
9. H1 long timing: decision hour is one of 07:00, 11:00, 15:00, or 19:00 UTC; H1 close is above EMA50; EMA21 is at or above EMA50; H1 24-bar and 6-bar log returns are non-negative; the candle is bullish; close location is at or above 0.58.
10. H1 short timing: decision hour is one of 07:00, 11:00, 15:00, or 19:00 UTC; H1 close is below EMA50; EMA21 is at or below EMA50; H1 24-bar and 6-bar log returns are non-positive; the candle is bearish; close location is at or below 0.42.
11. Frequency control: at most one signal per UTC day and direction.
12. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
13. Stop: 1.10 H1 ATR14 from the estimated entry price.
14. Target: fixed 1.50R target.
15. Time stop: 144 M5 bars, matching a 12-hour maximum planned holding window.

## Expected Behavior

This candidate should only pass if the fixed macro composite provides a directional prior that survives H1 trend-continuation timing across Capital.com, Pepperstone, and Dukascopy after costs. It should fail if the earlier macro-composite strength was only a low-sample artifact or if H1 broadening dilutes the signal.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by shifted macro-composite state plus H1 trend-continuation timing.

## Why This Hypothesis Should Exist

The earlier H4 macro-composite v0 was one of the few independent candidates to reach 6/9 PF cells with all cells positive, but it failed sample-size, concentration, and activity. The H1 macro-composite pullback version was too narrow and produced insufficient trades. This candidate tests a broader H1 continuation timing rule while preserving the pre-existing fixed macro vote definitions.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one macro regime, or one calendar window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the macro vote thresholds, H1 timing rule, stop size, target, or frequency rule after seeing this v0 result.
