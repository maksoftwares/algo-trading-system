# H1 Calendar Drift State v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h1_calendar_drift_state_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because the learned hour-of-week drift failed the multi-cell PF survival gate and breached catastrophic loss limits in the Capital.com and Dukascopy windows.

Hypothesis SHA256: `2d4f59cd062d8e68dcab24e5e3fc7cd0837f1f51c974a0dbae87189d2f4f5102`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 802 to 1209 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | Failed cells 1, 2, 3, 7, 8, and 9 | FAIL |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed in all cells | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 876 | 0.841 | -29.582 | 32.900 | 42.01% |
| 2 | capital_com | median | 876 | 0.841 | -29.582 | 32.900 | 42.01% |
| 3 | capital_com | p95 | 876 | 0.813 | -34.275 | 35.835 | 42.01% |
| 4 | pepperstone | best_case | 802 | 1.107 | 25.403 | 9.793 | 44.89% |
| 5 | pepperstone | median | 802 | 1.107 | 25.403 | 9.793 | 44.89% |
| 6 | pepperstone | p95 | 802 | 1.087 | 20.198 | 9.704 | 44.76% |
| 7 | dukascopy | best_case | 1209 | 0.919 | -21.061 | 33.822 | 43.01% |
| 8 | dukascopy | median | 1209 | 0.876 | -30.348 | 40.726 | 42.93% |
| 9 | dukascopy | p95 | 1209 | 0.784 | -47.472 | 53.072 | 41.60% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h1_calendar_drift_state_v0` in place. Any future calendar-drift revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This tested a different information source: UTC hour-of-week drift. The result shows there is plenty of activity, but the drift is not robust enough under the Phase 0 acceptance standard. The active Phase 1 soak and Phase 2 readiness remain unchanged.
