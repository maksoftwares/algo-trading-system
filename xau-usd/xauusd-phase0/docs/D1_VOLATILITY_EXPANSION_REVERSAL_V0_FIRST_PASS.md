# D1 Volatility Expansion Reversal v0 First Pass

Status: `REJECTED_FIRST_PASS`

`d1_volatility_expansion_reversal_v0` was the second H4/D1 decision-timing diversification attempt after Review #5. It completed a hash-locked real 9-cell matrix run and is rejected without tuning.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 30 to 53 trades | FAIL |
| Catastrophic loss | Max drawdown and total return within limits | Max DD 5.25%, some cells negative | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed | FAIL |
| Activity | Max zero-trade months within cap | Passed | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 35 | 1.268 | 2.597 | 3.451 | 42.86% |
| 2 | capital_com | median | 35 | 1.268 | 2.597 | 3.451 | 42.86% |
| 3 | capital_com | p95 | 35 | 1.260 | 2.530 | 3.489 | 42.86% |
| 4 | pepperstone | best_case | 30 | 0.868 | -1.200 | 3.255 | 33.33% |
| 5 | pepperstone | median | 30 | 0.868 | -1.200 | 3.255 | 33.33% |
| 6 | pepperstone | p95 | 30 | 0.862 | -1.267 | 3.277 | 33.33% |
| 7 | dukascopy | best_case | 53 | 0.876 | -1.929 | 5.186 | 33.96% |
| 8 | dukascopy | median | 53 | 0.869 | -2.039 | 5.251 | 33.96% |
| 9 | dukascopy | p95 | 53 | 0.872 | -1.968 | 5.130 | 33.96% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `d1_volatility_expansion_reversal_v0` in place. Any future revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This adds a second true H4/D1 decision-timing attempt to the evidence base. It does not solve diversification. The project still has no approved independent, non-level edge family.
