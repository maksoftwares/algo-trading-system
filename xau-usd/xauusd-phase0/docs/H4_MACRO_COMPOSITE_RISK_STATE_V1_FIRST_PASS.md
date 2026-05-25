# H4 Macro Composite Risk State v1 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_macro_composite_risk_state_v1` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because only 3 of 9 cells reached PF 1.30, all passing cells were Pepperstone-only, concentration failed in every cell, and activity failed in three cells.

Hypothesis SHA256: `54ab6d033023cc710fbb8038c4d92c22785193fb5e727278c8c3b44350a58dbb`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 3 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 51 to 169 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1-9 | FAIL |
| Activity | Max zero-trade months <= 3 | Failed cells 4-6 | FAIL |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 51 | 0.988 | -0.158 | 2.689 | 41.18% |
| 2 | capital_com | median | 51 | 0.988 | -0.158 | 2.689 | 41.18% |
| 3 | capital_com | p95 | 51 | 0.982 | -0.233 | 2.738 | 41.18% |
| 4 | pepperstone | best_case | 78 | 1.300 | 5.418 | 3.374 | 42.31% |
| 5 | pepperstone | median | 78 | 1.300 | 5.418 | 3.374 | 42.31% |
| 6 | pepperstone | p95 | 78 | 1.300 | 5.403 | 3.395 | 42.31% |
| 7 | dukascopy | best_case | 169 | 0.992 | -0.345 | 6.669 | 40.24% |
| 8 | dukascopy | median | 169 | 0.979 | -0.894 | 6.955 | 40.24% |
| 9 | dukascopy | p95 | 169 | 0.968 | -1.370 | 7.117 | 40.24% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_macro_composite_risk_state_v1` in place. Any future macro-composite attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

v1 fixed the v0 sample-size blocker, but widened participation diluted the cross-broker edge and left only Pepperstone at PF >= 1.30. The active Phase 1 soak and Phase 2 readiness remain unchanged.
