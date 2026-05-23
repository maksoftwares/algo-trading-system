# H4 Inside Bar D1 Momentum Breakout v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_inside_bar_d1_momentum_breakout_v0` was the sixth H4/D1 decision-timing attempt and a non-retest H4 breakout structure. It completed a hash-locked real 9-cell matrix run and is rejected without tuning.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 2 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 71 to 100 trades | PASS |
| Catastrophic loss | Max drawdown and total return within limits | Max DD 4.64%, all cells positive | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed outside Capital.com | FAIL |
| Activity | Max zero-trade months within cap | Passed | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 100 | 1.317 | 7.891 | 3.807 | 47.00% |
| 2 | capital_com | median | 100 | 1.317 | 7.891 | 3.807 | 47.00% |
| 3 | capital_com | p95 | 100 | 1.289 | 7.228 | 3.856 | 47.00% |
| 4 | pepperstone | best_case | 76 | 1.053 | 1.044 | 3.913 | 40.79% |
| 5 | pepperstone | median | 76 | 1.053 | 1.044 | 3.913 | 40.79% |
| 6 | pepperstone | p95 | 76 | 1.041 | 0.806 | 3.941 | 40.79% |
| 7 | dukascopy | best_case | 71 | 1.102 | 1.848 | 4.594 | 43.66% |
| 8 | dukascopy | median | 71 | 1.094 | 1.697 | 4.637 | 43.66% |
| 9 | dukascopy | p95 | 71 | 1.098 | 1.732 | 4.460 | 43.66% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_inside_bar_d1_momentum_breakout_v0` in place. Any future revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This adds a sixth H4/D1 attempt to the evidence base. It does not solve diversification. It shows a small positive tendency, but not enough cross-venue strength to become a valid candidate.
