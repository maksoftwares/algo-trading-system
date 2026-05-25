# XAG Lead XAU Followthrough v0 First Pass

Status: `REJECTED_FIRST_PASS`

`xag_lead_xau_followthrough_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because no matrix cell reached PF 1.30.

Hypothesis SHA256: `9e4806bc6c47b6b7271cab805af50d6aef14b05dc15bcff60bd82d6dcf27d5a7`

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 816 to 887 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed all cells | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 816 | 0.936 | -13.360 | 20.698 | 41.42% |
| 2 | capital_com | median | 816 | 0.936 | -13.360 | 20.698 | 41.42% |
| 3 | capital_com | p95 | 816 | 0.909 | -18.515 | 23.054 | 41.42% |
| 4 | pepperstone | best_case | 833 | 0.916 | -17.919 | 26.730 | 39.14% |
| 5 | pepperstone | median | 833 | 0.916 | -17.919 | 26.730 | 39.14% |
| 6 | pepperstone | p95 | 833 | 0.898 | -21.499 | 29.118 | 39.14% |
| 7 | dukascopy | best_case | 887 | 1.013 | 3.002 | 17.874 | 42.16% |
| 8 | dukascopy | median | 887 | 0.973 | -5.776 | 21.496 | 42.16% |
| 9 | dukascopy | p95 | 887 | 0.908 | -18.480 | 29.598 | 42.16% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `xag_lead_xau_followthrough_v0` in place. Any future XAG lead-lag continuation attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This tested the opposite behavior from XAU/XAG relative-value reversion: silver-led continuation. It produced ample trades and acceptable activity, but the edge was not profitable enough after costs. The active Phase 1 soak and Phase 2 readiness remain unchanged.
