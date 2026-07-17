# MT5 R1B Strict Compression Dukascopy Portability V1 Result

Decision: **REJECT_R1B_PORTABILITY**

Research only. This does not authorize model training, EA consumption, demo orders, or live orders.

| Policy | Stage | Trades | Trades/day | Stress PF | Avg stress R | DD R | Top removed R | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `MT5_STACKING_DIAGNOSTIC` | `replication_fit` | 118 | 0.095 | 1.333 | 0.214 | 21.098 | 15.661 | FAIL |
| `MT5_STACKING_DIAGNOSTIC` | `development` | 55 | 0.059 | 1.860 | 0.448 | 13.716 | 15.138 | FAIL |
| `MT5_STACKING_DIAGNOSTIC` | `exam` | 86 | 0.138 | 3.244 | 0.847 | 15.842 | 63.253 | FAIL |
| `PORTFOLIO_CONSTRAINED_PRIMARY` | `replication_fit` | 32 | 0.026 | 1.771 | 0.434 | 8.172 | 4.430 | FAIL |
| `PORTFOLIO_CONSTRAINED_PRIMARY` | `development` | 22 | 0.024 | 1.588 | 0.338 | 5.753 | -1.967 | FAIL |
| `PORTFOLIO_CONSTRAINED_PRIMARY` | `exam` | 20 | 0.032 | 3.863 | 0.963 | 2.386 | 9.735 | PASS |

## Interpretation

R1B failed at least one frozen economic portability gate.
