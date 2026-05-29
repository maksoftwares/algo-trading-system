# H1 COT Positioning Continuation v0 First Pass

Status: REJECTED_FIRST_PASS
Date: 2026-05-29
Hypothesis SHA256: `cbdf39426049e671efd9a8aa11b5f1434c1589bc78d3fb8b773e28b2ba87c9ec`

`h1_cot_positioning_continuation_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It solved the prior COT reversal candidate's sample-size problem, but it did not show a persistent edge: 0/9 matrix cells reached PF >= 1.30.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best | 41 | 43.90% | 1.001 | 0.01% | 2.40% | 19 |
| 2 | Capital.com | median | 41 | 43.90% | 1.001 | 0.01% | 2.40% | 19 |
| 3 | Capital.com | p95 | 41 | 43.90% | 0.976 | -0.27% | 2.52% | 19 |
| 4 | Pepperstone | best | 58 | 37.93% | 0.816 | -3.07% | 3.85% | 3 |
| 5 | Pepperstone | median | 58 | 37.93% | 0.816 | -3.07% | 3.85% | 3 |
| 6 | Pepperstone | p95 | 58 | 37.93% | 0.805 | -3.26% | 3.83% | 3 |
| 7 | Dukascopy | best | 99 | 36.36% | 0.784 | -5.86% | 7.95% | 5 |
| 8 | Dukascopy | median | 99 | 36.36% | 0.766 | -6.37% | 8.24% | 5 |
| 9 | Dukascopy | p95 | 99 | 35.35% | 0.722 | -7.55% | 8.76% | 5 |

## Gate Read

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Trade-count cells | 9/9 | 9/9 | PASS |
| Max zero-trade months | 19 | <= 3 | FAIL |
| Cross-broker persistence | Capital near flat; Pepperstone/Dukascopy negative | Broadly positive | FAIL |

## Decision

Reject v0 and do not proceed to deciles, multisymbol, intrabar, or Gate 9 review. Any future COT continuation work must use a new versioned hypothesis and a fresh SHA256 lock.
