# H1 GLD Flow Momentum Pullback v0 First Pass

Status: REJECTED_FIRST_PASS
Date: 2026-05-29
Hypothesis SHA256: `01b1f5cfefbc7d0f38a9559387678bf26296d6a46de823144277910f9fb78bc1`

`h1_gld_flow_momentum_pullback_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It tested whether shifted GLD ETF flow shocks work better as continuation information than the prior GLD-flow reversal attempts. The answer was no: all 9 cells had PF below 1.30.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best | 66 | 33.33% | 0.569 | -8.24% | 9.72% | 3 |
| 2 | Capital.com | median | 66 | 33.33% | 0.569 | -8.24% | 9.72% | 3 |
| 3 | Capital.com | p95 | 66 | 33.33% | 0.554 | -8.56% | 9.79% | 3 |
| 4 | Pepperstone | best | 67 | 38.81% | 0.893 | -2.00% | 5.16% | 2 |
| 5 | Pepperstone | median | 67 | 38.81% | 0.893 | -2.00% | 5.16% | 2 |
| 6 | Pepperstone | p95 | 67 | 38.81% | 0.884 | -2.18% | 5.23% | 2 |
| 7 | Dukascopy | best | 59 | 35.59% | 0.800 | -3.31% | 4.23% | 7 |
| 8 | Dukascopy | median | 59 | 35.59% | 0.779 | -3.66% | 4.46% | 7 |
| 9 | Dukascopy | p95 | 59 | 35.59% | 0.738 | -4.33% | 5.03% | 7 |

## Gate Read

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Trade-count cells | 9/9 | 9/9 | PASS |
| Max zero-trade months | 7 | <= 3 | FAIL |
| Cross-broker persistence | All broker windows negative | Broadly positive | FAIL |

## Decision

Reject v0 and do not proceed to deciles, multisymbol, intrabar, or Gate 9 review. This also weakens the GLD-flow proxy lane: the narrow reversal v0 had PF but not sample size, reversal v1 diluted PF, and this flow-aligned continuation v0 solved sample size but had 0/9 PF cells.
