# D1 Multi-Day Exhaustion Reversion v0 First Pass

Status: `REJECTED_FIRST_PASS`

`d1_multi_day_exhaustion_reversion_v0` was the fourth true H4/D1 decision-timing diversification attempt and the second testable Review #6 candidate after `h4_real_yield_proxy_momentum_v0` was blocked by missing macro data. It completed a hash-locked real 9-cell matrix run and is rejected without tuning.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 24 to 41 trades | FAIL |
| Catastrophic loss | Max drawdown and total return within limits | Max DD 4.56%, six cells negative | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed | FAIL |
| Activity | Max zero-trade months within cap | Some cells reached 4 zero-trade months | FAIL |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 41 | 1.234 | 2.646 | 1.947 | 41.46% |
| 2 | capital_com | median | 41 | 1.234 | 2.646 | 1.947 | 41.46% |
| 3 | capital_com | p95 | 41 | 1.227 | 2.566 | 1.978 | 41.46% |
| 4 | pepperstone | best_case | 32 | 0.672 | -3.337 | 4.520 | 28.12% |
| 5 | pepperstone | median | 32 | 0.672 | -3.337 | 4.520 | 28.12% |
| 6 | pepperstone | p95 | 32 | 0.667 | -3.403 | 4.563 | 28.12% |
| 7 | dukascopy | best_case | 24 | 0.978 | -0.150 | 3.553 | 37.50% |
| 8 | dukascopy | median | 24 | 0.970 | -0.205 | 3.579 | 37.50% |
| 9 | dukascopy | p95 | 24 | 0.924 | -0.523 | 3.631 | 37.50% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `d1_multi_day_exhaustion_reversion_v0` in place. Any future revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This adds a fourth true H4/D1 decision-timing attempt to the evidence base. It does not solve diversification. The project still has no approved independent, non-level edge family.
