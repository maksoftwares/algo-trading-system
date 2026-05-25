# H4 Policy Uncertainty Safe Haven v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_policy_uncertainty_safe_haven_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because only 3 of 9 cells reached PF 1.30, all passing cells were Pepperstone-only, and concentration failed in six cells.

Hypothesis SHA256: `fc6af0eb01a84a394d5da471f2b43e725127dc167f670d5a7a197fa983cb6822`

Data source: FRED `USEPUINDXD` daily US Economic Policy Uncertainty Index.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 3 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 142 to 181 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1-3 and 7-9 | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 142 | 1.168 | 6.034 | 4.921 | 42.96% |
| 2 | capital_com | median | 142 | 1.168 | 6.034 | 4.921 | 42.96% |
| 3 | capital_com | p95 | 142 | 1.152 | 5.438 | 4.993 | 42.96% |
| 4 | pepperstone | best_case | 158 | 1.530 | 18.542 | 3.236 | 49.37% |
| 5 | pepperstone | median | 158 | 1.530 | 18.542 | 3.236 | 49.37% |
| 6 | pepperstone | p95 | 158 | 1.523 | 18.313 | 3.256 | 49.37% |
| 7 | dukascopy | best_case | 181 | 1.054 | 2.373 | 8.439 | 39.23% |
| 8 | dukascopy | median | 181 | 1.037 | 1.630 | 8.461 | 39.23% |
| 9 | dukascopy | p95 | 181 | 1.014 | 0.589 | 8.491 | 39.23% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_policy_uncertainty_safe_haven_v0` in place. Any future policy-uncertainty or macro-stress attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This lane cleared the missing-data blocker for public policy-uncertainty data and produced enough trades, but the expectancy was broker-local rather than cross-venue. The active Phase 1 soak and Phase 2 readiness remain unchanged.
