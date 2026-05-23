# D1 Compression H4 Expansion v0 First Pass

Status: `REJECTED_FIRST_PASS`

`d1_compression_h4_expansion_v0` was the third true H4/D1 decision-timing diversification attempt from the Review #6 plan. It completed a hash-locked real 9-cell matrix run and is rejected without tuning.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 68 to 122 trades | PASS |
| Catastrophic loss | Max drawdown and total return within limits | Max DD 5.99%, six cells negative | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed | FAIL |
| Activity | Max zero-trade months within cap | Passed | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 71 | 0.780 | -4.686 | 5.834 | 30.99% |
| 2 | capital_com | median | 71 | 0.780 | -4.686 | 5.834 | 30.99% |
| 3 | capital_com | p95 | 71 | 0.770 | -4.885 | 5.986 | 30.99% |
| 4 | pepperstone | best_case | 68 | 0.863 | -2.603 | 5.566 | 32.35% |
| 5 | pepperstone | median | 68 | 0.863 | -2.603 | 5.566 | 32.35% |
| 6 | pepperstone | p95 | 68 | 0.865 | -2.548 | 5.470 | 32.35% |
| 7 | dukascopy | best_case | 122 | 1.289 | 9.034 | 3.340 | 43.44% |
| 8 | dukascopy | median | 122 | 1.279 | 8.642 | 3.363 | 43.44% |
| 9 | dukascopy | p95 | 122 | 1.244 | 7.594 | 3.383 | 43.44% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `d1_compression_h4_expansion_v0` in place. Any future revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This adds a third true H4/D1 decision-timing attempt to the evidence base. It does not solve diversification. The project still has no approved independent, non-level edge family.
