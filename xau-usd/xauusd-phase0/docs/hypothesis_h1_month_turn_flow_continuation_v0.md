# H1 Month-Turn Flow Continuation v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: calendar-flow / month-turn trend continuation
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 48-144
Expected median hold hours: 4-12
Expected decisions per week: 1-8 during month-turn windows
Timeframe diversification qualifies: yes
Expected trade count per year: 120-900
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-75%
Expected worst single month: -8R to -24R
Expected max consecutive zero months: 2
Expected R-multiple distribution: month-turn flows should create directional persistence only near month start/end; reject if the effect is a generic weak trend-following filter or only one-broker pocket.

## Mechanical Definition

This candidate is a research-only month-turn flow-continuation hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG, GLD-flow, COT, futures-volume, macro-composite, volatility-squeeze, learned-state, or hour-of-week drift strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H1 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. Month-turn window: a completed H1 bar qualifies only when UTC day-of-month is 1-4 or 25-31.
4. Decision hours: 07:00, 11:00, 15:00, or 19:00 UTC only.
5. Long state: H1 close is above EMA50, EMA21 is at or above EMA50, H1 24-bar log return is at least +0.0010, H1 6-bar log return is not below -0.0005, the candle is bullish, and close location is at or above 0.56.
6. Short state: H1 close is below EMA50, EMA21 is at or below EMA50, H1 24-bar log return is at most -0.0010, H1 6-bar log return is not above +0.0005, the candle is bearish, and close location is at or below 0.44.
7. Frequency control: at most one signal per UTC day and direction.
8. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
9. Stop: 1.05 H1 ATR14 from the estimated entry price.
10. Target: fixed 1.50R target.
11. Time stop: 144 M5 bars, matching a 12-hour maximum planned holding window.

## Expected Behavior

This candidate should only pass if month-turn flow windows create directional persistence beyond ordinary H1 trend following across Capital.com, Pepperstone, and Dukascopy after costs. It should fail if the calendar window is too broad, if the effect is one-broker only, or if it is simply a noisy trend filter.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by month-turn timing plus H1 trend continuation.

## Why This Hypothesis Should Exist

The search has tested many market-state proxies without finding independent approval. Month-start and month-end windows are a different information class: recurring institutional flow timing rather than price-level geometry, macro proxy state, or ETF/COT data. This v0 tests whether that flow timing is enough to improve a simple H1 continuation rule.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one month-turn subwindow, or one calendar window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the month-day window, H1 timing rule, stop size, target, or frequency rule after seeing this v0 result.
