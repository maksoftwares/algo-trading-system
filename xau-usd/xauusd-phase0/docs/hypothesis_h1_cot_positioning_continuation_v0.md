# H1 COT Positioning Continuation v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: futures-positioning / positioning-aligned continuation
Entry / decision timeframe: H1 completed-candle decision with weekly CFTC COT state and M5 execution sequencing
Expected median hold bars M5-equivalent: 48-144
Expected median hold hours: 4-12
Expected decisions per week: 1-10
Timeframe diversification qualifies: yes
Expected trade count per year: 100-800
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-75%
Expected worst single month: -8R to -22R
Expected max consecutive zero months: 2
Expected R-multiple distribution: COT state should bias direction, while H1 pullbacks provide timing; reject if the edge only appears on one broker, one COT regime, or one calendar pocket.

## Mechanical Definition

This candidate is a research-only CFTC Commitments of Traders positioning-continuation hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG, FX proxy, ETF-flow, futures-volume, volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H1 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. External positioning source: CFTC disaggregated futures-only Commitments of Traders annual files for GOLD - COMMODITY EXCHANGE INC., CFTC contract market code `088691`.
4. No-lookahead rule: each COT report is treated as usable only from report date plus 6 calendar days.
5. COT features:
   - managed-money net share of open interest: `(managed_money_long_all - managed_money_short_all) / open_interest_all`
   - producer/merchant net share of open interest: `(producer_long_all - producer_short_all) / open_interest_all`
   - rolling 156-report percentile ranks for both net-share series
   - 4-report change in managed-money net share
6. Long COT state: managed-money net percentile is at or above 0.60, producer net percentile is at or below 0.55, and managed-money net share has risen over the last 4 reports.
7. Short COT state: managed-money net percentile is at or below 0.40, producer net percentile is at or above 0.45, and managed-money net share has fallen over the last 4 reports.
8. H1 long continuation timing: decision hour is one of 07:00, 11:00, 15:00, or 19:00 UTC; H1 close is at or above EMA50; EMA21 is at or above EMA50; H1 24-bar log return is not worse than -0.0020; the completed candle touches EMA21 within the ATR band; the candle is bullish; close location is at or above 0.55.
9. H1 short continuation timing: decision hour is one of 07:00, 11:00, 15:00, or 19:00 UTC; H1 close is at or below EMA50; EMA21 is at or below EMA50; H1 24-bar log return is not better than 0.0020; the completed candle touches EMA21 within the ATR band; the candle is bearish; close location is at or below 0.45.
10. Frequency control: at most one signal per UTC day and direction.
11. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
12. Stop: 1.15 H1 ATR14 from the estimated entry price.
13. Target: fixed 1.50R target.
14. Time stop: 144 M5 bars, matching a 12-hour maximum planned holding window.

## Expected Behavior

This candidate should only pass if weekly futures positioning adds a directional prior that improves H1 pullback-continuation timing across all three broker windows after costs. It should fail if COT is too delayed, if H1 timing adds no edge, or if the evidence is concentrated in a single broker or calendar window.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked COT positioning state plus H1 pullback timing.

## Why This Hypothesis Should Exist

The prior COT reversal v0 was too low-frequency and failed all matrix cells. This v0 tests the opposite behavioral claim: when managed money is increasing exposure in a gold trend, continuation after H1 pullbacks may survive better than fading the positioning extreme. It is independent from the approved breakout-retest family because its primary state variable is official futures positioning, not spot level retest geometry.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one COT regime, or one calendar window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the COT percentile thresholds, 4-report direction rule, H1 timing rule, stop size, target, or frequency rule after seeing this v0 result.
