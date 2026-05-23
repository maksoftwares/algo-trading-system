# H4 D1 Momentum Expansion Continuation v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h4_d1_momentum_expansion_continuation_v0` was the fifth true H4/D1 decision-timing diversification attempt. It completed a hash-locked real 9-cell matrix run and is rejected without tuning.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 3 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 81 to 83 trades | PASS |
| Catastrophic loss | Max drawdown and total return within limits | Max DD 3.86%, three cells negative | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed | FAIL |
| Activity | Max zero-trade months within cap | Passed | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 81 | 1.169 | 3.456 | 3.431 | 44.44% |
| 2 | capital_com | median | 81 | 1.169 | 3.456 | 3.431 | 44.44% |
| 3 | capital_com | p95 | 81 | 1.159 | 3.261 | 3.470 | 44.44% |
| 4 | pepperstone | best_case | 81 | 0.905 | -2.016 | 3.862 | 38.27% |
| 5 | pepperstone | median | 81 | 0.905 | -2.016 | 3.862 | 38.27% |
| 6 | pepperstone | p95 | 81 | 0.907 | -1.967 | 3.793 | 38.27% |
| 7 | dukascopy | best_case | 83 | 1.376 | 7.197 | 2.399 | 46.99% |
| 8 | dukascopy | median | 83 | 1.353 | 6.746 | 2.321 | 46.99% |
| 9 | dukascopy | p95 | 83 | 1.304 | 5.828 | 2.505 | 46.99% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h4_d1_momentum_expansion_continuation_v0` in place. Any future revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This adds a fifth true H4/D1 decision-timing attempt to the evidence base. It does not solve diversification. Performance was venue-fragile, with all PF >= 1.30 cells coming from Dukascopy only.
