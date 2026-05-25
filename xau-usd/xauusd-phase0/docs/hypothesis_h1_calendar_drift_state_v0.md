# H1 Calendar Drift State v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: Learned UTC hour-of-week drift
Entry / decision timeframe: H1 completed-candle decision, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 36-144
Expected median hold hours: 3-12
Expected decisions per week: 1-12
Timeframe diversification qualifies: yes
Expected trade count per year: 40-320
Expected cost-adjusted PF: 1.03-1.35
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many small calendar-seasonality misses near -1R, fewer +1.35R winners, and rejection if drift is one-window-only.

## Mechanical Definition

This candidate is a research-only learned calendar-drift hypothesis for XAUUSD. It is not a retest, reclaim, round-number, daily/weekly level, session-extreme, VWAP, sweep, inside-day, outside-day, broad-USD proxy, gold/silver relative-value, M5 path-skew, tick-volume, fixed autocorrelation-state, or walk-forward linear multi-feature model.

The intended mechanical setup is:

1. Market and decision timeframe: XAUUSD H1 bars only.
2. Execution timeframe: M5 bars are used only by the existing simulator for market-entry and exit sequencing.
3. Calendar bucket: completed H1 bar timestamp is mapped to UTC hour-of-week, from 0 to 167.
4. Label: for historical rows only, label the next 6 completed H1 bars of ATR-normalized forward return.
5. Walk-forward rule: at each scoring point, use only prior rows from the same hour-of-week bucket whose 6-bar future label is already fully known before the current signal timestamp.
6. Training window: use a fixed trailing window of completed H1 bars.
7. Observation gate: no setup until the same hour-of-week bucket has the locked minimum number of prior observations.
8. Long setup: the same-bucket historical mean forward return and significance score exceed the locked positive thresholds.
9. Short setup: the same-bucket historical mean forward return and significance score exceed the locked negative thresholds.
10. Frequency control: take at most one signal per UTC day and direction.
11. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
12. Stop: ATR-based XAUUSD stop using only completed H1 data.
13. Target: fixed R multiple selected in the locked implementation before any result-producing run.
14. Invalidation: no setup if timestamps, ATR, same-bucket history, or stop/target construction are invalid.

## Expected Behavior

Expected behavior is weak but repeatable intraday/weekly calendar drift. The candidate should only pass if any hour-of-week effect survives across Capital.com, Pepperstone, and Dukascopy under measured costs.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must be reproducible from local data and the locked hour-of-week recipe.

## Why This Hypothesis Should Exist

After many price-structure candidates failed, a pure time-of-week drift model tests a different information source: calendar microstructure. It uses no price levels, no external data, no discretionary filters, and no post-result tuning. It is also auditable because every score comes from prior same-bucket observations only.

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
- Any future improvement changes the calendar bucket, label horizon, training window, thresholds, or stop/target recipe after results are known without creating a new versioned hypothesis.
