# H1 GLD Flow Stress Follow-Through v0 First Pass

Status: REJECTED_FIRST_PASS
Date: 2026-05-29
Hypothesis SHA256: `ae0e45c48e834ff10ce71164f7cc9a0273abb02158cea67277742e952394be13`

`h1_gld_flow_stress_followthrough_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. The candidate tested whether high-volume GLD ETF flow shocks create same-direction H1 XAU follow-through rather than reversal. It solved the sample-size problem, but failed first-pass expectancy: only 2/9 cells reached PF >= 1.30, and the passing cells were Dukascopy best/median only.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best | 89 | 37.08% | 0.801 | -4.93% | 6.65% | 3 |
| 2 | Capital.com | median | 89 | 37.08% | 0.801 | -4.93% | 6.65% | 3 |
| 3 | Capital.com | p95 | 89 | 37.08% | 0.778 | -5.52% | 6.84% | 3 |
| 4 | Pepperstone | best | 82 | 43.90% | 1.221 | 4.47% | 3.95% | 1 |
| 5 | Pepperstone | median | 82 | 43.90% | 1.221 | 4.47% | 3.95% | 1 |
| 6 | Pepperstone | p95 | 82 | 43.90% | 1.201 | 4.07% | 4.00% | 1 |
| 7 | Dukascopy | best | 71 | 47.89% | 1.329 | 5.17% | 2.50% | 5 |
| 8 | Dukascopy | median | 71 | 47.89% | 1.301 | 4.72% | 2.55% | 5 |
| 9 | Dukascopy | p95 | 71 | 47.89% | 1.233 | 3.65% | 2.66% | 5 |

## Gate Read

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 2/9 | 7/9 | FAIL |
| Trade-count cells | 9/9 | 9/9 | PASS |
| Max zero-trade months | 5 | <= 3 | FAIL |
| Cross-broker persistence | Capital failed; Pepperstone sub-threshold; Dukascopy best/median only | Broadly positive above threshold | FAIL |

## Decision

Reject v0 and do not proceed to deciles, multisymbol, intrabar, or Gate 9 review. The GLD-flow follow-through interpretation improved activity but did not produce cross-broker PF strength.
