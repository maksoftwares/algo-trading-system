# H1 Return Autocorrelation State v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h1_return_autocorrelation_state_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because it failed the multi-cell PF survival gate. Trade count was strong, so this is an expectancy failure rather than a data-frequency blocker.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 148 to 193 trades | PASS |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | Max DD 13.17%, worst return -12.55% | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed in all cells | FAIL |
| Activity | Max zero-trade months <= 3 | 0 months | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 158 | 0.991 | -0.416 | 8.877 | 39.24% |
| 2 | capital_com | median | 158 | 0.991 | -0.416 | 8.877 | 39.24% |
| 3 | capital_com | p95 | 158 | 0.969 | -1.396 | 9.225 | 39.24% |
| 4 | pepperstone | best_case | 148 | 1.234 | 9.930 | 4.623 | 42.57% |
| 5 | pepperstone | median | 148 | 1.234 | 9.930 | 4.623 | 42.57% |
| 6 | pepperstone | p95 | 148 | 1.224 | 9.492 | 4.708 | 41.89% |
| 7 | dukascopy | best_case | 193 | 0.830 | -9.611 | 10.891 | 34.72% |
| 8 | dukascopy | median | 193 | 0.811 | -10.688 | 11.628 | 34.72% |
| 9 | dukascopy | p95 | 193 | 0.776 | -12.546 | 13.166 | 34.72% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h1_return_autocorrelation_state_v0` in place. Any future modeled-state revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This was a useful modeled-thinking test. The locked return-state score produced plenty of trades and one stronger broker window, but it did not generalize across Capital.com, Pepperstone, and Dukascopy. The active Phase 1 soak and Phase 2 readiness remain unchanged.
