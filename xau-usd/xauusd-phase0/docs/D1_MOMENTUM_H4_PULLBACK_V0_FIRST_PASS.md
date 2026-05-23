# D1 Momentum H4 Pullback v0 First Pass

Status: `REJECTED_FIRST_PASS`

`d1_momentum_h4_pullback_v0` was the first Review #5-forced candidate that genuinely used H4/D1 decision timing instead of M5 entries around a slower reference level. It completed a hash-locked real 9-cell matrix run and is rejected without tuning.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 3 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 69 to 80 trades | PASS |
| Catastrophic loss | Max drawdown and total return within limits | Max DD 4.74%, all cells positive | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed | FAIL |
| Activity | Max zero-trade months within cap | Passed | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 80 | 1.282 | 6.545 | 2.835 | 40.00% |
| 2 | capital_com | median | 80 | 1.282 | 6.545 | 2.835 | 40.00% |
| 3 | capital_com | p95 | 80 | 1.255 | 5.967 | 2.946 | 40.00% |
| 4 | pepperstone | best_case | 69 | 1.395 | 7.897 | 3.494 | 36.23% |
| 5 | pepperstone | median | 69 | 1.395 | 7.897 | 3.494 | 36.23% |
| 6 | pepperstone | p95 | 69 | 1.358 | 7.183 | 3.548 | 36.23% |
| 7 | dukascopy | best_case | 79 | 1.173 | 3.896 | 4.503 | 36.71% |
| 8 | dukascopy | median | 79 | 1.156 | 3.534 | 4.560 | 36.71% |
| 9 | dukascopy | p95 | 79 | 1.146 | 3.260 | 4.743 | 36.71% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `d1_momentum_h4_pullback_v0` in place. Any future revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Review #5 Impact

This run closes the immediate forcing-function requirement: a genuinely non-level, H4/D1-timed candidate was registered, hash-locked, implemented, smoke-tested, and run through a result-producing first pass before any new same-family candidate was authored.

It does not solve diversification. The project still has no approved independent, non-level edge family.
