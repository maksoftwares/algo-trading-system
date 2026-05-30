# H1 GVZ/VIX Volatility-Premium Follow-Through v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_gvz_vix_vol_premium_followthrough_v0` without tuning.

This candidate tested whether shifted GVZ/VIX gold-volatility premium supports H1 XAUUSD follow-through after spot has already moved in the premium-aligned direction. It solved sample size across all broker/cost cells, but it failed persistence with 0/9 PF cells above 1.30 and every broker window negative after costs.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 157 | 38.85% | 0.8967 | -4.48% | 9.92% | 6 | FAIL |
| 2 | capital_com | median | 157 | 38.85% | 0.8967 | -4.48% | 9.92% | 6 | FAIL |
| 3 | capital_com | p95 | 157 | 38.85% | 0.8809 | -5.18% | 10.29% | 6 | FAIL |
| 4 | pepperstone | best_case | 238 | 33.19% | 0.7355 | -18.59% | 23.47% | 4 | FAIL |
| 5 | pepperstone | median | 238 | 33.19% | 0.7355 | -18.59% | 23.47% | 4 | FAIL |
| 6 | pepperstone | p95 | 238 | 33.19% | 0.7258 | -19.28% | 24.06% | 4 | FAIL |
| 7 | dukascopy | best_case | 247 | 39.68% | 0.9447 | -3.79% | 8.77% | 7 | FAIL |
| 8 | dukascopy | median | 247 | 39.68% | 0.9214 | -5.36% | 8.96% | 7 | FAIL |
| 9 | dukascopy | p95 | 247 | 39.68% | 0.8794 | -8.05% | 9.55% | 7 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 1,926 | Informational | PASS |
| Max zero-trade months | 7 | <= 3 | FAIL |
| Cross-broker persistence | All broker/cost windows negative | Robust positive edge | FAIL |
| Best observed PF | 0.9447 | >= 1.30 in most cells | FAIL |

## Interpretation

The paired GVZ/VIX premium follow-through expression is not an edge under the current evidence set. It was active enough to be testable, but the directionality was wrong across all three broker windows and worsened under P95 cost.

## Next Action

Do not tune v0. Treat this as evidence that shifted daily GVZ/VIX relative volatility premium, by itself, is not sufficient to create an independent XAU H1 follow-through expert.
