# H4 GLD ETF Flow Reversal v1 First Pass

Generated: 2026-05-29
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h4_gld_etf_flow_reversal_v1` without tuning. This result-informed v1 did solve the v0 trade-count problem, but the broader GLD-flow definition diluted the PF edge. No matrix cell reached PF >= 1.30.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Zero months | Single trade % | Top 5 % |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | capital_com | best_case | 60 | 46.67% | 0.9804 | -0.22% | 2 | 100.00% | 100.00% |
| 2 | capital_com | median | 60 | 46.67% | 0.9804 | -0.22% | 2 | 100.00% | 100.00% |
| 3 | capital_com | p95 | 60 | 46.67% | 0.9655 | -0.39% | 2 | 100.00% | 100.00% |
| 4 | pepperstone | best_case | 86 | 44.19% | 0.9485 | -0.98% | 2 | 100.00% | 100.00% |
| 5 | pepperstone | median | 86 | 44.19% | 0.9485 | -0.98% | 2 | 100.00% | 100.00% |
| 6 | pepperstone | p95 | 86 | 43.02% | 0.9415 | -1.11% | 2 | 100.00% | 100.00% |
| 7 | dukascopy | best_case | 61 | 45.90% | 1.1944 | 2.49% | 3 | 31.01% | 150.69% |
| 8 | dukascopy | median | 61 | 45.90% | 1.1721 | 2.22% | 3 | 34.04% | 166.87% |
| 9 | dukascopy | p95 | 61 | 45.90% | 1.1432 | 1.85% | 3 | 40.48% | 197.35% |

## Gate Snapshot

| Gate | Result |
|---|---|
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | PASS, 9/9 |
| Max zero-trade months <= 3 | PASS, max 3 |
| Concentration | FAIL |
| Cost sensitivity | Not promoted to deeper review |

## Audit Note

This v1 was explicitly result-informed from `h4_gld_etf_flow_reversal_v0`, which had 9/9 PF cells but failed activity and concentration. The broader v1 result shows that the v0 PF strength did not survive broader sampling.

## Next Action

Do not tune v1. Continue the EA hunt in a different mechanism lane.
