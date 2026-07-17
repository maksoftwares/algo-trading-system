# XAUUSD M30 Chop Dukascopy Portability V1 Result

Decision: **CHOP_M30_DUKASCOPY_PORTABILITY_REJECTED**

Frozen Capital.com candidate replayed unchanged on verified Dukascopy Bid/Ask data.

| Stage | Trades | Trades/day | PF | Stress PF | Stress avg R | Stress net R | DD R | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| train | 74 | 0.048 | 1.269 | 0.824 | -0.112 | -8.264 | 12.444 | FAIL |
| validation | 50 | 0.054 | 1.347 | 0.952 | -0.027 | -1.351 | 8.101 | FAIL |
| exam | 29 | 0.046 | 1.004 | 0.791 | -0.127 | -3.695 | 6.590 | FAIL |
| full | 153 | 0.049 | 1.239 | 0.857 | -0.087 | -13.310 | 18.939 | FAIL |

## Interpretation

The unchanged specialist failed at least one frozen cross-venue gate. It is not rescued or tuned in V1.

Research only. No Python prediction, EA, demo, live, or broker authorization is granted.
