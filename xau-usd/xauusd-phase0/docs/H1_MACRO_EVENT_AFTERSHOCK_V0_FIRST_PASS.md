# H1 Macro Event Aftershock v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h1_macro_event_aftershock_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because 0 of 9 cells reached PF 1.30 and concentration failed in every cell.

Hypothesis SHA256: `c77f2b603f4c1150895ca7f206be794b2a8185cd3c522770a530cfe2a0b43220`

Event schedule: deterministic standardized US macro event slots for first-Friday NFP, second-Wednesday CPI, and selected third-Wednesday FOMC proxy windows.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 85 to 93 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | All cells meet threshold | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Failed cells 1-9 | FAIL |
| Activity | Max zero-trade months <= 3 | All cells meet threshold | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | All broker pairs meet threshold | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 93 | 0.989 | -0.256 | 3.270 | 45.16% |
| 2 | capital_com | median | 93 | 0.989 | -0.256 | 3.270 | 45.16% |
| 3 | capital_com | p95 | 93 | 0.961 | -0.932 | 3.338 | 45.16% |
| 4 | pepperstone | best_case | 85 | 0.950 | -1.111 | 4.510 | 43.53% |
| 5 | pepperstone | median | 85 | 0.950 | -1.111 | 4.510 | 43.53% |
| 6 | pepperstone | p95 | 85 | 0.922 | -1.729 | 4.823 | 43.53% |
| 7 | dukascopy | best_case | 92 | 1.036 | 0.832 | 3.140 | 44.57% |
| 8 | dukascopy | median | 92 | 0.952 | -1.102 | 3.133 | 43.48% |
| 9 | dukascopy | p95 | 92 | 0.898 | -2.337 | 3.721 | 43.48% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h1_macro_event_aftershock_v0` in place. Any future event-regime attempt needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

The event-regime idea produced enough trades and was not cost-fragile, but the first aftershock continuation rule had no cross-cell expectancy. This argues against approving a simple scheduled-event continuation EA in the current data.
