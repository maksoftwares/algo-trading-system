# H1 M5 Path Skew Reversal v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h1_m5_path_skew_reversal_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because it failed the multi-cell PF survival gate. Trade count was very strong, so this is an expectancy failure rather than a data-frequency blocker.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 498 to 644 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | Max DD 22.11%, worst return -19.21% | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed in all cells | FAIL |
| Activity | Max zero-trade months <= 3 | 0 months | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 498 | 0.894 | -14.602 | 19.633 | 39.96% |
| 2 | capital_com | median | 498 | 0.894 | -14.602 | 19.633 | 39.96% |
| 3 | capital_com | p95 | 498 | 0.870 | -17.729 | 21.956 | 39.96% |
| 4 | pepperstone | best_case | 498 | 1.066 | 8.940 | 13.612 | 43.37% |
| 5 | pepperstone | median | 498 | 1.066 | 8.940 | 13.612 | 43.37% |
| 6 | pepperstone | p95 | 498 | 1.043 | 5.733 | 15.169 | 43.37% |
| 7 | dukascopy | best_case | 644 | 0.963 | -6.660 | 14.455 | 40.99% |
| 8 | dukascopy | median | 644 | 0.939 | -10.737 | 16.928 | 40.99% |
| 9 | dukascopy | p95 | 644 | 0.885 | -19.205 | 22.108 | 40.99% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h1_m5_path_skew_reversal_v0` in place. Any future M5 path-structure revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This was useful because it tested a distinct M5 path-formation information class. Late absorption inside an H1 candle produced many opportunities but did not produce robust cross-broker edge. The active Phase 1 soak and Phase 2 readiness remain unchanged.
