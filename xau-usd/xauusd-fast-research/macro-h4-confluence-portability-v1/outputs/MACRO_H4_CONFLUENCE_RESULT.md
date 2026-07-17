# XAUUSD H4 Macro Confluence Dukascopy Portability V1

Decision: **MACRO_H4_CONFLUENCE_PORTABILITY_REJECTED**

The unchanged Phase 0 specialist was replayed with native Dukascopy Bid/Ask execution.

| Stage | Trades | L/S | Trades/day | PF | Stress PF | Stress avg R | Stress net R | DD R | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| train | 13 | 8/5 | 0.008 | 1.922 | 1.409 | 0.162 | 2.101 | 2.618 | FAIL |
| validation | 23 | 2/21 | 0.025 | 0.767 | 0.585 | -0.220 | -5.071 | 6.965 | FAIL |
| exam | 3 | 1/2 | 0.007 | 0.449 | 0.376 | -0.449 | -1.347 | 2.161 | FAIL |
| full | 39 | 11/28 | 0.013 | 1.025 | 0.779 | -0.111 | -4.317 | 7.648 | FAIL |

## Interpretation

The unchanged macro specialist failed at least one frozen gate and is not tuned or rescued in V1.

Research only. No Python prediction, EA, demo, live, or broker authorization is granted.
