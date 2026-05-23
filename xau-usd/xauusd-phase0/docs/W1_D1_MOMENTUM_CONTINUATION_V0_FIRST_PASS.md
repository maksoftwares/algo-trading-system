# W1 D1 Momentum Continuation v0 First Pass

Status: `REJECTED_FIRST_PASS`

`w1_d1_momentum_continuation_v0` was the first W1/D1-scale diversification attempt after six H4/D1 first-pass rejections. It completed a hash-locked real 9-cell matrix run and is rejected without tuning.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 3 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 48 to 68 trades | PASS |
| Catastrophic loss | Max drawdown and total return within limits | Max DD 2.96%, all cells positive | PASS |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed | FAIL |
| Activity | Max zero-trade months within cap | Passed | PASS |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Passed | PASS |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 50 | 1.430 | 4.440 | 2.172 | 48.00% |
| 2 | capital_com | median | 50 | 1.430 | 4.440 | 2.172 | 48.00% |
| 3 | capital_com | p95 | 50 | 1.424 | 4.386 | 2.181 | 48.00% |
| 4 | pepperstone | best_case | 48 | 1.275 | 2.871 | 1.988 | 47.92% |
| 5 | pepperstone | median | 48 | 1.275 | 2.871 | 1.988 | 47.92% |
| 6 | pepperstone | p95 | 48 | 1.272 | 2.838 | 1.993 | 47.92% |
| 7 | dukascopy | best_case | 68 | 1.081 | 1.192 | 2.900 | 41.18% |
| 8 | dukascopy | median | 68 | 1.078 | 1.147 | 2.920 | 41.18% |
| 9 | dukascopy | p95 | 68 | 1.070 | 1.039 | 2.958 | 41.18% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `w1_d1_momentum_continuation_v0` in place. Any future revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This adds a first W1/D1-scale attempt to the evidence base. It is the best-behaved higher-timeframe rejection so far because all cells were positive and trade counts passed, but it still lacks the cross-venue PF strength and concentration quality required for approval.
