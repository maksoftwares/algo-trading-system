# MT5 Compression Breakout Dukascopy Portability V1 Result

Decision: **REJECT_PORTABILITY**

Research only. This does not authorize model training, EA consumption, demo orders, or live orders.

## Stage Metrics

| Policy | Stage | Trades | Trades/day | Stress PF | Avg stress R | DD R | Top removed R | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `MT5_STACKING_DIAGNOSTIC` | `replication_fit` | 424 | 0.341 | 1.171 | 0.114 | 75.354 | 38.625 | FAIL |
| `MT5_STACKING_DIAGNOSTIC` | `development` | 263 | 0.282 | 1.017 | 0.012 | 61.647 | -6.465 | FAIL |
| `MT5_STACKING_DIAGNOSTIC` | `exam` | 202 | 0.324 | 2.516 | 0.672 | 30.280 | 125.975 | FAIL |
| `PORTFOLIO_CONSTRAINED_PRIMARY` | `replication_fit` | 126 | 0.101 | 0.899 | -0.075 | 32.052 | -19.029 | FAIL |
| `PORTFOLIO_CONSTRAINED_PRIMARY` | `development` | 78 | 0.084 | 1.147 | 0.097 | 13.401 | -1.953 | FAIL |
| `PORTFOLIO_CONSTRAINED_PRIMARY` | `exam` | 53 | 0.085 | 1.874 | 0.456 | 7.888 | 14.551 | PASS |

## Interpretation

The portfolio-constrained rule failed at least one frozen Dukascopy stability gate. The MT5 headline is not portable enough for specialist qualification.
