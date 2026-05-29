# H1 Macro Composite Pullback v0 First Pass

Generated: 2026-05-29
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_macro_composite_pullback_v0` without tuning. It was a transparent result-informed attempt to convert the H4 macro-composite near miss into a higher-sample H1 timing candidate. It did not solve the sample-size problem and only 3/9 cells reached PF >= 1.30.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Zero months |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | capital_com | best_case | 10 | 40.00% | 0.9454 | -0.16% | 14 |
| 2 | capital_com | median | 10 | 40.00% | 0.9454 | -0.16% | 14 |
| 3 | capital_com | p95 | 10 | 40.00% | 0.9106 | -0.26% | 14 |
| 4 | pepperstone | best_case | 9 | 66.67% | 3.7659 | 3.12% | 10 |
| 5 | pepperstone | median | 9 | 66.67% | 3.7659 | 3.12% | 10 |
| 6 | pepperstone | p95 | 9 | 66.67% | 3.7215 | 3.09% | 10 |
| 7 | dukascopy | best_case | 29 | 48.28% | 1.1508 | 1.03% | 12 |
| 8 | dukascopy | median | 29 | 48.28% | 1.1306 | 0.90% | 12 |
| 9 | dukascopy | p95 | 29 | 48.28% | 1.0857 | 0.59% | 12 |

## Gate Snapshot

| Gate | Result |
|---|---|
| PF >= 1.30 in at least 7/9 cells | FAIL, 3/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Max zero-trade months <= 2 | FAIL, max 14 |
| Concentration | FAIL |
| Cost sensitivity | Not promoted to deeper review |

## Next Action

Do not tune v0. The H1 macro timing version did not improve the H4 macro-composite near miss enough to become a new EA candidate.
