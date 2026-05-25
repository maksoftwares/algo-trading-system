# H1 Walk Forward Linear State v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h1_walk_forward_linear_state_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. A blocker was fixed before final scoring: constant/unavailable tick-count z-score is treated as neutral `0.0`, matching the hypothesis wording that tick-count is used only when available. The corrected first pass is rejected because the learned H1 state failed the multi-cell PF survival gate.

Hypothesis SHA256: `1670603d68fb013a5118e8f388f97a65d7ca3642240bd776612994f2bff5a9d8`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 561 to 788 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | Max DD 19.16%, worst return -14.31% | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1, 2, 3, 4, 5, 6, and 9 | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 561 | 0.923 | -11.362 | 17.097 | 39.39% |
| 2 | capital_com | median | 561 | 0.923 | -11.362 | 17.097 | 39.39% |
| 3 | capital_com | p95 | 561 | 0.902 | -14.323 | 19.162 | 39.39% |
| 4 | pepperstone | best_case | 644 | 1.070 | 12.715 | 12.988 | 39.75% |
| 5 | pepperstone | median | 644 | 1.070 | 12.715 | 12.988 | 39.75% |
| 6 | pepperstone | p95 | 644 | 1.050 | 9.000 | 13.588 | 39.75% |
| 7 | dukascopy | best_case | 788 | 1.113 | 27.130 | 11.920 | 42.64% |
| 8 | dukascopy | median | 788 | 1.092 | 21.384 | 12.409 | 42.64% |
| 9 | dukascopy | p95 | 788 | 1.042 | 9.362 | 13.470 | 42.51% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h1_walk_forward_linear_state_v0` in place. Any future learned-state attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This was the first deterministic AI-style learned-state lane. The negative result is still useful: after the blocker fix, the model traded all broker windows with healthy sample size, but none of the 9 cells reached PF 1.30. The active Phase 1 soak and Phase 2 readiness remain unchanged.
