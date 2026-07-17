# MT5 R1 Uptrend Specialist Dukascopy Portability V1 Result

Decision: **R1_NEAR_SURVIVOR_REJECT_INSUFFICIENT_SAMPLE**

Research only. This does not authorize model training, EA consumption, demo orders, or live orders.

## Stage Metrics

| Policy | Stage | Trades | Trades/day | Stress PF | Avg stress R | DD R | Top removed R | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `MT5_STACKING_DIAGNOSTIC` | `replication_fit` | 146 | 0.117 | 1.611 | 0.348 | 19.581 | 41.179 | FAIL |
| `MT5_STACKING_DIAGNOSTIC` | `development` | 64 | 0.069 | 1.861 | 0.450 | 11.717 | 19.234 | PASS |
| `MT5_STACKING_DIAGNOSTIC` | `exam` | 130 | 0.208 | 2.768 | 0.742 | 15.909 | 86.780 | FAIL |
| `PORTFOLIO_CONSTRAINED_PRIMARY` | `replication_fit` | 48 | 0.039 | 1.965 | 0.490 | 6.699 | 14.037 | PASS |
| `PORTFOLIO_CONSTRAINED_PRIMARY` | `development` | 28 | 0.030 | 1.805 | 0.436 | 4.555 | 2.694 | FAIL |
| `PORTFOLIO_CONSTRAINED_PRIMARY` | `exam` | 41 | 0.066 | 2.911 | 0.778 | 3.696 | 22.263 | PASS |

## Interpretation

The constrained R1 mechanism passed every frozen economic and concentration gate, but failed a minimum-sample gate. It remains an unqualified near-survivor; no threshold is relaxed and additional prospective evidence is required.
