# M15 Two Bar Exhaustion Reversal v0 First Pass

Status: `REJECTED_FIRST_PASS`

`m15_two_bar_exhaustion_reversal_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because no matrix cell reached PF 1.30 and catastrophic loss limits were breached in the Capital.com, Pepperstone P95, and Dukascopy windows.

Hypothesis SHA256: `c455057dd8ea55dba9e441502ab58aa4323887b1057e1060d670009c7b99d41e`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 1304 to 1454 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | Failed cells 1, 2, 3, 6, 7, 8, and 9 | FAIL |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed in all cells | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 1336 | 0.684 | -66.785 | 67.238 | 44.54% |
| 2 | capital_com | median | 1336 | 0.684 | -66.785 | 67.238 | 44.54% |
| 3 | capital_com | p95 | 1336 | 0.600 | -76.939 | 77.186 | 44.46% |
| 4 | pepperstone | best_case | 1304 | 0.973 | -9.030 | 18.832 | 44.56% |
| 5 | pepperstone | median | 1304 | 0.973 | -9.030 | 18.832 | 44.56% |
| 6 | pepperstone | p95 | 1304 | 0.868 | -36.944 | 38.417 | 44.56% |
| 7 | dukascopy | best_case | 1454 | 0.803 | -58.307 | 59.693 | 40.44% |
| 8 | dukascopy | median | 1454 | 0.713 | -71.678 | 71.992 | 40.44% |
| 9 | dukascopy | p95 | 1454 | 0.546 | -86.142 | 86.199 | 40.23% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `m15_two_bar_exhaustion_reversal_v0` in place. Any future M15 exhaustion-reversal revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This tested a non-level M15 snapback behavior. The result shows high activity but no robust edge. The active Phase 1 soak and Phase 2 readiness remain unchanged.
