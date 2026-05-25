# H4 Macro Composite Risk State v1 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v1
Author / owner: maksoftwares / Codex
Mechanic family: fixed macro composite / AI-style risk-state vote
Entry / decision timeframe: H4 completed-candle decision with shifted daily/weekly macro state and M5 execution sequencing
Expected median hold bars M5-equivalent: 72-432
Expected median hold hours: 6-36
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 45-220
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 40%-80%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Composite macro-state attempts should be selective but not ultra-sparse; reject if behavior is one-broker-only, one-crisis-only, or needs post-result threshold edits.

## Mechanical Definition

This candidate is a new versioned macro-composite hypothesis. It does not alter `h4_macro_composite_risk_state_v0`, which remains rejected. It is not a trained model, not an optimized ensemble, not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG relative-value, FX proxy-only, real-yield-only, breakeven-only, Treasury-curve-only, credit-spread-only, COT positioning, GVZ-only, VIX-only, financial-conditions-only, price-only volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v1 setup is:

1. Market and decision timeframe: XAUUSD H4 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. External state inputs are the same transparent FRED input families as v0: `DFII10`, `DTWEXBGS`, `T5YIE`, `T10YIE`, `DGS2`, `DGS10`, `T10Y2Y`, `BAA10Y`, `AAA10Y`, `VIXCLS`, `GVZCLS`, `NFCI`, and `ANFCI`.
4. No-lookahead rule: all external macro features are shifted by one observation before they are merged into H4 bars.
5. Every input vote has weight 1. There is no fitting, no learned coefficient, and no threshold selected by a machine optimizer.
6. Bullish and bearish vote definitions are unchanged from v0.
7. Composite score: bullish vote count minus bearish vote count.
8. Long macro state: composite score >= +2 and bullish vote count >= 3.
9. Short macro state: composite score <= -2 and bearish vote count >= 3.
10. Long H4 confirmation: H4 close is above EMA40, the completed H4 candle is bullish, and 6-H4 log return is positive.
11. Short H4 confirmation: H4 close is below EMA40, the completed H4 candle is bearish, and 6-H4 log return is negative.
12. Frequency control: at most one signal per UTC day and direction.
13. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
14. Stop: 1.20 H4 ATR14 from the estimated entry price.
15. Target: fixed 1.65R target.
16. Time stop: 432 M5 bars, matching a 36-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if a broader-but-still-cross-domain macro vote produces enough observations without collapsing into noisy one-family trading. It should fail if increasing coverage weakens cross-broker PF survival, leaves Capital.com below sample, or leaves concentration/activity unresolved.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked vote table plus H4 momentum confirmation.

## Why This Hypothesis Should Exist

The v0 macro composite was rejected, but it was the first independent macro lane to show broad positive cells and 6/9 PF cells >= 1.30. This v1 is a separately locked attempt to test whether requiring at least three same-side macro votes while reducing the net-score cutoff from 3 to 2 can improve sample size without abandoning cross-domain agreement.

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
- Any future improvement changes the vote table, composite threshold, H4 confirmation, stop size, target, or frequency rule after seeing this v1 result.
