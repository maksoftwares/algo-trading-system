# H4 Walk Forward KNN Momentum State v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_walk_forward_knn_momentum_state_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. A neutral blocker was fixed before final scoring: nullable feature columns are coerced to numeric arrays before nearest-neighbor distance calculations. The corrected first pass is rejected because no matrix cell reached PF 1.30.

Hypothesis SHA256: `297b9bd82f1a2212cc4ebfe91228bbdfd6739dff00df42f39c02d3f95e2c37ed`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 485 to 652 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed all cells | FAIL |
| Activity | Max zero-trade months <= 3 | Failed all cells | FAIL |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 485 | 1.048 | 4.525 | 6.199 | 49.69% |
| 2 | capital_com | median | 485 | 1.048 | 4.525 | 6.199 | 49.69% |
| 3 | capital_com | p95 | 485 | 1.023 | 2.161 | 6.958 | 49.07% |
| 4 | pepperstone | best_case | 534 | 1.104 | 10.149 | 6.035 | 50.19% |
| 5 | pepperstone | median | 534 | 1.104 | 10.149 | 6.035 | 50.19% |
| 6 | pepperstone | p95 | 534 | 1.084 | 8.187 | 6.191 | 50.19% |
| 7 | dukascopy | best_case | 652 | 1.009 | 1.133 | 12.046 | 41.87% |
| 8 | dukascopy | median | 652 | 0.980 | -2.528 | 12.876 | 41.72% |
| 9 | dukascopy | p95 | 652 | 0.938 | -7.693 | 14.300 | 41.41% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_walk_forward_knn_momentum_state_v0` in place. Any future AI-style or nearest-neighbor attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This tested the owner-requested AI-style lane in a deterministic, auditable form. The method is operationally safe, but it did not produce a tradable edge under Phase 0 gates. The active Phase 1 soak and Phase 2 readiness remain unchanged.
