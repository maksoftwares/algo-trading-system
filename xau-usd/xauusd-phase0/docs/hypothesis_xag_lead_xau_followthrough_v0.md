# XAG Lead XAU Followthrough v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: intermarket lead-lag continuation
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 36-216
Expected median hold hours: 3-18
Expected decisions per week: 2-20
Timeframe diversification qualifies: yes
Expected trade count per year: 100-700
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-70%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many small failed follow-through entries, fewer +1.45R winners, and rejection if silver leadership is unstable after costs.

## Mechanical Definition

This candidate is a research-only H1 XAG-to-XAU lead-lag continuation hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, calendar-drift, learned-state, or relative-value reversion strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H1 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. Required proxy input: broker-consistent XAGUSD H1 bars for the same Phase 0 cell.
4. Lead features: XAG 6-hour and 24-hour log returns, XAU 6-hour and 24-hour log returns, XAG minus XAU relative impulse, and rolling relative-impulse z-score.
5. Trend context: XAU H1 EMA20 and ATR14.
6. Long setup: XAG has a positive 6-hour and 24-hour impulse, XAG leads XAU by a positive relative-impulse z-score, and the current XAU H1 candle confirms upward follow-through near or above EMA20.
7. Short setup: XAG has a negative 6-hour and 24-hour impulse, XAG leads XAU lower by a negative relative-impulse z-score, and the current XAU H1 candle confirms downward follow-through near or below EMA20.
8. Frequency control: at most one signal per UTC day and direction.
9. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
10. Stop: 1.00 H1 ATR from estimated entry.
11. Target: fixed 1.45R target.
12. Time stop: 216 M5 bars, matching an 18-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if silver impulses consistently lead gold follow-through across broker/date cells. It should fail if silver leadership is only a local correlation artifact or if costs erase the delayed XAU move.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked XAG lead and XAU confirmation rule.

## Why This Hypothesis Should Exist

The existing XAU/XAG candidate tested relative-value reversion and failed. This hypothesis tests the opposite behavior family: whether silver impulse leadership can forecast gold continuation without using price levels or the approved breakout-retest mechanism.

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
- Any future improvement changes the lead-lag windows, thresholds, stop size, target, or frequency rule after seeing this v0 result.
