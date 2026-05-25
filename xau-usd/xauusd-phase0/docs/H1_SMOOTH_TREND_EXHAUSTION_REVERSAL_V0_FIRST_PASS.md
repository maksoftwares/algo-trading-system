# H1 Smooth Trend Exhaustion Reversal v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h1_smooth_trend_exhaustion_reversal_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because it failed the multi-cell PF survival gate. Trade count was adequate, so this is an expectancy failure rather than a data-frequency blocker.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 42 to 77 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | Max DD 10.21%, worst return -8.11% | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed | FAIL |
| Activity | Max zero-trade months <= 3 | 2 to 3 months | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 42 | 0.643 | -4.669 | 8.399 | 33.33% |
| 2 | capital_com | median | 42 | 0.643 | -4.669 | 8.399 | 33.33% |
| 3 | capital_com | p95 | 42 | 0.631 | -4.837 | 8.525 | 33.33% |
| 4 | pepperstone | best_case | 43 | 0.905 | -1.133 | 2.440 | 41.86% |
| 5 | pepperstone | median | 43 | 0.905 | -1.133 | 2.440 | 41.86% |
| 6 | pepperstone | p95 | 43 | 0.889 | -1.319 | 2.545 | 41.86% |
| 7 | dukascopy | best_case | 77 | 0.708 | -6.693 | 9.160 | 33.77% |
| 8 | dukascopy | median | 77 | 0.689 | -7.161 | 9.523 | 33.77% |
| 9 | dukascopy | p95 | 77 | 0.647 | -8.107 | 10.208 | 33.77% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h1_smooth_trend_exhaustion_reversal_v0` in place. Any future revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This was useful because it separated a data blocker from a real behavior test. The candidate did not need any new broker data and still failed cleanly on expectancy across all three matrix windows. The result strengthens the current conclusion that simple XAU-only non-level reversal behavior is not enough by itself.
