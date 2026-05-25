# COT Gold Positioning Reversal v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: futures-positioning / sentiment extreme reversal
Entry / decision timeframe: H4 completed-candle decision with weekly CFTC COT state and M5 execution sequencing
Expected median hold bars M5-equivalent: 144-576
Expected median hold hours: 12-48
Expected decisions per week: 0-2
Timeframe diversification qualifies: yes
Expected trade count per year: 35-120
Expected cost-adjusted PF: 1.05-1.50
Expected losing-month percentage: 40%-75%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Positioning extremes should create moderate-frequency reversal attempts with many small failures and fewer 1.70R winners; reject if the behavior is one-window or one-broker only.

## Mechanical Definition

This candidate is a research-only CFTC Commitments of Traders positioning hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG, FX proxy, real-yield proxy, volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H4 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. External positioning source: CFTC disaggregated futures-only Commitments of Traders annual files for GOLD - COMMODITY EXCHANGE INC., CFTC contract market code `088691`.
4. No-lookahead rule: each COT report is treated as usable only from the following Monday 00:00 UTC after the Tuesday report date.
5. COT features:
   - managed-money net share of open interest: `(managed_money_long_all - managed_money_short_all) / open_interest_all`
   - producer/merchant net share of open interest: `(producer_long_all - producer_short_all) / open_interest_all`
   - rolling 156-report percentile ranks for both net-share series
   - 4-report change in managed-money net share
6. Long positioning state: managed-money net percentile is at or below 0.30, producer net percentile is at or above 0.70, and managed-money net share has risen over the last 4 reports.
7. Short positioning state: managed-money net percentile is at or above 0.70, producer net percentile is at or below 0.30, and managed-money net share has fallen over the last 4 reports.
8. Long H4 confirmation: H4 close is above EMA40, the completed H4 candle is bullish, and 6-H4 log return is positive.
9. Short H4 confirmation: H4 close is below EMA40, the completed H4 candle is bearish, and 6-H4 log return is negative.
10. Frequency control: at most one signal per COT report week and direction.
11. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
12. Stop: 1.25 H4 ATR14 from the estimated entry price.
13. Target: fixed 1.70R target.
14. Time stop: 576 M5 bars, matching a 48-hour maximum planned holding window.

## Expected Behavior

The candidate should only pass if futures positioning extremes add information that survives across Capital.com, Pepperstone, and Dukascopy windows after costs. It should fail if COT is too delayed, already reflected in price, or only captures a small number of large gold trend reversals.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked COT positioning state plus H4 confirmation.

## Why This Hypothesis Should Exist

The current search has exhausted the obvious XAU-only, intermarket, volatility, learned-state, and macro real-yield lanes without finding an independent EA. CFTC COT data is a genuinely different information class: weekly futures positioning from market participants, not broker-specific spot-gold price structure.

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
- Any future improvement changes the percentile thresholds, 4-report turn rule, H4 confirmation, stop size, target, or frequency rule after seeing this v0 result.
