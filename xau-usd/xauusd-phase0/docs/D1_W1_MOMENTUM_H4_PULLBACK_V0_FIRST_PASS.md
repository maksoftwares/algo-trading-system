# D1 W1 Momentum H4 Pullback v0 First Pass

Status: `REJECTED_FIRST_PASS`

`d1_w1_momentum_h4_pullback_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because only the three Dukascopy cells reached PF 1.30 and concentration failed in all cells.

Hypothesis SHA256: `a4f07bcff42c1130277319e4438a19175c5be5a73e6f4705dac8e288bb44f66c`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 3 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 53 to 67 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed all cells | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 64 | 1.132 | 2.449 | 2.962 | 40.63% |
| 2 | capital_com | median | 64 | 1.132 | 2.449 | 2.962 | 40.63% |
| 3 | capital_com | p95 | 64 | 1.112 | 2.078 | 3.075 | 40.63% |
| 4 | pepperstone | best_case | 53 | 1.191 | 2.770 | 3.129 | 39.62% |
| 5 | pepperstone | median | 53 | 1.191 | 2.770 | 3.129 | 39.62% |
| 6 | pepperstone | p95 | 53 | 1.187 | 2.698 | 3.109 | 39.62% |
| 7 | dukascopy | best_case | 67 | 1.506 | 8.355 | 2.957 | 46.27% |
| 8 | dukascopy | median | 67 | 1.489 | 8.110 | 2.998 | 46.27% |
| 9 | dukascopy | p95 | 67 | 1.462 | 7.672 | 3.161 | 46.27% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `d1_w1_momentum_h4_pullback_v0` in place. Any future D1/W1/H4 revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This is the strongest new independent lead in this batch, but it is not an EA. The signal survived only in the latest Dukascopy window and failed the 7-of-9 PF standard. The active Phase 1 soak and Phase 2 readiness remain unchanged.
