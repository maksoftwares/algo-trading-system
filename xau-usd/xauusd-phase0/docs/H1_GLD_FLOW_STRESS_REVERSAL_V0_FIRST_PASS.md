# H1 GLD Flow Stress Reversal v0 First Pass

Status: REJECTED_FIRST_PASS
Date: 2026-05-29
Hypothesis SHA256: `8af7b2e8956d784fbb382fb7f41aacdb8ea6a4e333916d553311dbb16fd67c1f`

`h1_gld_flow_stress_reversal_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. The candidate attempted to broaden the earlier H4 GLD-flow reversal lead into completed H1 reversal timing. It failed first pass: only the Dukascopy window showed PF strength, 0/9 cells met the 40-trade minimum, and max zero-trade months reached 10.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best | 27 | 40.74% | 0.949 | -0.36% | 4.49% | 9 |
| 2 | Capital.com | median | 27 | 40.74% | 0.949 | -0.36% | 4.49% | 9 |
| 3 | Capital.com | p95 | 27 | 40.74% | 0.934 | -0.48% | 4.55% | 9 |
| 4 | Pepperstone | best | 22 | 31.82% | 0.711 | -1.92% | 3.72% | 10 |
| 5 | Pepperstone | median | 22 | 31.82% | 0.711 | -1.92% | 3.72% | 10 |
| 6 | Pepperstone | p95 | 22 | 31.82% | 0.710 | -1.92% | 3.71% | 10 |
| 7 | Dukascopy | best | 29 | 65.52% | 2.411 | 6.63% | 1.84% | 10 |
| 8 | Dukascopy | median | 29 | 65.52% | 2.305 | 6.16% | 1.86% | 10 |
| 9 | Dukascopy | p95 | 29 | 65.52% | 2.198 | 5.76% | 1.88% | 10 |

## Gate Read

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 3/9 | 7/9 | FAIL |
| Trade-count cells | 0/9 | 9/9 | FAIL |
| Max zero-trade months | 10 | <= 3 | FAIL |
| Cross-broker persistence | Dukascopy-only strength; Capital/Pepperstone failed | Broadly positive above threshold | FAIL |

## Decision

Reject v0 and do not proceed to deciles, multisymbol, intrabar, or Gate 9 review. The H1 broadening did not preserve the H4 GLD-flow edge across brokers and remained too sparse.
