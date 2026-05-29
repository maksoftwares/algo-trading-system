# H1 Macro Composite Trend Continuation v0 First Pass

Status: REJECTED_FIRST_PASS
Date: 2026-05-29
Hypothesis SHA256: `a7f6d5363715baca1739c87a421504ac050d9d2c1b4cf8fed6def359a47d2761`

`h1_macro_composite_trend_continuation_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It broadened the earlier H1 macro-composite pullback candidate into a trend-continuation timing rule. The candidate showed a Pepperstone-only pocket of strength, but it did not pass first-pass gates: only 3/9 cells reached PF >= 1.30 and only 6/9 cells met the 40-trade minimum.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best | 38 | 44.74% | 0.956 | -0.45% | 2.96% | 5 |
| 2 | Capital.com | median | 38 | 44.74% | 0.956 | -0.45% | 2.96% | 5 |
| 3 | Capital.com | p95 | 38 | 44.74% | 0.938 | -0.64% | 2.97% | 5 |
| 4 | Pepperstone | best | 52 | 48.08% | 1.440 | 5.51% | 1.70% | 7 |
| 5 | Pepperstone | median | 52 | 48.08% | 1.440 | 5.51% | 1.70% | 7 |
| 6 | Pepperstone | p95 | 52 | 48.08% | 1.424 | 5.32% | 1.69% | 7 |
| 7 | Dukascopy | best | 113 | 45.13% | 1.156 | 4.32% | 3.32% | 2 |
| 8 | Dukascopy | median | 113 | 45.13% | 1.110 | 3.03% | 3.55% | 2 |
| 9 | Dukascopy | p95 | 113 | 44.25% | 1.051 | 1.38% | 4.23% | 2 |

## Gate Read

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 3/9 | 7/9 | FAIL |
| Trade-count cells | 6/9 | 9/9 | FAIL |
| Max zero-trade months | 7 | <= 3 | FAIL |
| Cross-broker persistence | Pepperstone passed; Capital failed; Dukascopy below threshold | Broadly positive above threshold | FAIL |

## Decision

Reject v0 and do not proceed to deciles, multisymbol, intrabar, or Gate 9 review. This result preserves the earlier observation that macro-composite features can create isolated positive windows, but the behavior is not sufficiently broad or active for Phase 0 approval.
