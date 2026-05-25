# M15 Two Bar Impulse Continuation v0 First Pass

Status: `REJECTED_FIRST_PASS`

`m15_two_bar_impulse_continuation_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because no matrix cell reached PF 1.30 and catastrophic loss limits were breached in the Capital.com and Dukascopy P95 windows.

Hypothesis SHA256: `ea24f37e7f30e6a3045b82745a069ab6ff802538de1924e40b591fdfc3ed5515`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 1192 to 1310 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | Failed cells 1, 2, 3, 8, and 9 | FAIL |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed in all cells | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 1229 | 0.889 | -22.342 | 31.946 | 46.05% |
| 2 | capital_com | median | 1229 | 0.889 | -22.342 | 31.946 | 46.05% |
| 3 | capital_com | p95 | 1229 | 0.857 | -28.127 | 35.838 | 45.65% |
| 4 | pepperstone | best_case | 1192 | 0.977 | -5.459 | 21.024 | 47.15% |
| 5 | pepperstone | median | 1192 | 0.977 | -5.459 | 21.024 | 47.15% |
| 6 | pepperstone | p95 | 1192 | 0.953 | -11.055 | 23.146 | 46.98% |
| 7 | dukascopy | best_case | 1310 | 0.934 | -15.452 | 24.894 | 46.56% |
| 8 | dukascopy | median | 1310 | 0.889 | -25.011 | 28.585 | 46.03% |
| 9 | dukascopy | p95 | 1308 | 0.814 | -38.245 | 39.325 | 45.03% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `m15_two_bar_impulse_continuation_v0` in place. Any future M15 impulse-continuation revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This tested a non-level M15 impulse-persistence behavior. It performed better than the snapback version but still failed the Phase 0 acceptance standard. The active Phase 1 soak and Phase 2 readiness remain unchanged.
