# H1 GLD Flow Momentum Pullback v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: ETF-flow / flow-aligned momentum continuation
Entry / decision timeframe: H1 completed-candle decision with shifted GLD daily OHLCV flow state and M5 execution sequencing
Expected median hold bars M5-equivalent: 48-144
Expected median hold hours: 4-12
Expected decisions per week: 1-12
Timeframe diversification qualifies: yes
Expected trade count per year: 120-900
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-75%
Expected worst single month: -8R to -22R
Expected max consecutive zero months: 2
Expected R-multiple distribution: GLD flow should provide a directional prior while H1 pullbacks provide timing; reject if the behavior is one-broker, one-window, or only a high-frequency mirage.

## Mechanical Definition

This candidate is a research-only GLD ETF flow-aligned momentum hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, XAU/XAG, FX proxy, COT, futures-volume, macro-composite, volatility-squeeze, calendar-drift, or learned-state strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H1 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. External flow source: public Yahoo daily GLD ETF OHLCV proxy file `data/reference/etf/gld_daily_yahoo_2015_2025.csv`.
4. No-lookahead rule: GLD daily features are shifted by one completed daily observation before merging into XAU H1 bars.
5. GLD flow features:
   - one-day GLD log return
   - rolling 252-day volume percentile
   - rolling 126-day log-volume z-score
   - rolling 126-day log-dollar-volume z-score
6. Flow-active state: GLD volume percentile is at or above 0.75, max(volume z-score, dollar-volume z-score) is at or above 0.80, and absolute one-day GLD return is at least 0.0030.
7. Long flow state: flow-active and GLD one-day return is at or above +0.0030.
8. Short flow state: flow-active and GLD one-day return is at or below -0.0030.
9. H1 long timing: decision hour is one of 07:00, 11:00, 15:00, or 19:00 UTC; H1 close is at or above EMA50; EMA21 is at or above EMA50; H1 24-bar log return is not worse than -0.0015; the completed candle touches EMA21 within the ATR band; the candle is bullish; close location is at or above 0.55.
10. H1 short timing: decision hour is one of 07:00, 11:00, 15:00, or 19:00 UTC; H1 close is at or below EMA50; EMA21 is at or below EMA50; H1 24-bar log return is not better than 0.0015; the completed candle touches EMA21 within the ATR band; the candle is bearish; close location is at or below 0.45.
11. Frequency control: at most one signal per UTC day and direction.
12. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
13. Stop: 1.10 H1 ATR14 from the estimated entry price.
14. Target: fixed 1.50R target.
15. Time stop: 144 M5 bars, matching a 12-hour maximum planned holding window.

## Expected Behavior

This candidate should only pass if shifted GLD ETF flow gives a directional prior that survives through H1 pullback-continuation timing across Capital.com, Pepperstone, and Dukascopy after costs. It should fail if the GLD signal is already fully priced, if it only works in one broker window, or if broader sampling dilutes the earlier narrow GLD-flow PF lead.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by shifted GLD flow state plus H1 pullback timing.

## Why This Hypothesis Should Exist

The GLD ETF flow reversal v0 was the strongest independent PF lead so far but failed sample size. The broader GLD-flow reversal v1 solved sample size and diluted to 0/9 PF cells. This v0 tests a different claim before abandoning the data class: high-volume GLD flow shocks may be momentum information, not fade information, when XAU later offers an H1 pullback.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one broker, one GLD-flow pocket, or one calendar window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement changes the GLD thresholds, H1 timing rule, stop size, target, or frequency rule after seeing this v0 result.
