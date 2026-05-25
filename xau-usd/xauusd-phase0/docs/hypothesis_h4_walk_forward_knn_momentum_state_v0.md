# H4 Walk Forward KNN Momentum State v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: auditable walk-forward nearest-neighbor momentum state
Entry / decision timeframe: H4 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 36-144
Expected median hold hours: 3-12
Expected decisions per week: 1-10
Timeframe diversification qualifies: yes
Expected trade count per year: 80-500
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many small failed state trades, fewer +1.30R wins, and rejection if nearest-neighbor fit only works in one venue/date window.

## Mechanical Definition

This candidate is a research-only H4 walk-forward nearest-neighbor momentum-state hypothesis. It is not a retest, reclaim, round-number, session-extreme, VWAP, sweep, intermarket proxy, calendar-drift, or hand-tuned level strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD H4 completed bars.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. Features: H4 1/3/6-bar returns normalized by ATR, H4 range/body/close-position features, D1 5/20-bar momentum normalized by ATR, D1 range, and D1 close position.
4. Label: H4 close-to-close return over the next 3 completed H4 bars, normalized by current H4 ATR.
5. Walk-forward boundary: for any current H4 decision, labels are only available for training rows whose 3-H4-bar forward label completed before the current bar.
6. Training window: last 1800 eligible H4 bars.
7. Neighbors: nearest 60 prior states by squared distance over the locked feature vector.
8. Long setup: neighbor mean forward return is at least +0.18 ATR and score is at least +1.15.
9. Short setup: neighbor mean forward return is at most -0.18 ATR and score is at most -1.15.
10. Frequency control: at most one signal per UTC day and direction.
11. Entry: market entry at the first available M5 execution bar at or after the completed H4 signal timestamp.
12. Stop: 0.95 H4 ATR from estimated entry.
13. Target: fixed 1.30R target.
14. Time stop: 144 M5 bars, matching the 3-H4-bar label horizon.

## Expected Behavior

The candidate should only pass if a simple, auditable state memory improves over the previously rejected linear and calendar learned-state candidates. It should fail when similar-looking H4/D1 momentum states do not repeat after costs.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked H4/D1 state vector and walk-forward neighbor rule.

## Why This Hypothesis Should Exist

The project owner asked whether AI-style thinking could be integrated into the search. This is a constrained version of that idea: it uses nearest-neighbor state memory, but every decision remains deterministic, auditable, and free of current-bar lookahead.

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
- Any future improvement changes the neighbor count, thresholds, feature set, or horizon after seeing this v0 result.
