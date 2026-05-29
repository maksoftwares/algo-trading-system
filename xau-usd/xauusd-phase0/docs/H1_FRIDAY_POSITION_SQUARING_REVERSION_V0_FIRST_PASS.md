# H1 Friday Position-Squaring Reversion v0 First Pass

Status: REJECTED_FIRST_PASS
Date: 2026-05-29
Hypothesis SHA256: `649634442f273a177fee7817165dd9142a8bcc79cecd369035960e9b33d0999e`

`h1_friday_position_squaring_reversion_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. The candidate tested whether Friday US-session position reduction after a one-day directional move creates an independent XAUUSD reversion edge. It failed first pass: 0/9 cells reached PF >= 1.30, only 3/9 cells met the 40-trade minimum, and Pepperstone/Dukascopy were negative.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best | 34 | 50.00% | 1.127 | 0.94% | 1.45% | 3 |
| 2 | Capital.com | median | 34 | 50.00% | 1.127 | 0.94% | 1.45% | 3 |
| 3 | Capital.com | p95 | 34 | 50.00% | 1.097 | 0.73% | 1.48% | 3 |
| 4 | Pepperstone | best | 29 | 41.38% | 0.796 | -1.51% | 2.78% | 4 |
| 5 | Pepperstone | median | 29 | 41.38% | 0.796 | -1.51% | 2.78% | 4 |
| 6 | Pepperstone | p95 | 29 | 41.38% | 0.793 | -1.53% | 2.74% | 4 |
| 7 | Dukascopy | best | 43 | 32.56% | 0.329 | -7.70% | 7.89% | 3 |
| 8 | Dukascopy | median | 43 | 32.56% | 0.315 | -7.94% | 8.10% | 3 |
| 9 | Dukascopy | p95 | 43 | 32.56% | 0.298 | -8.17% | 8.30% | 3 |

## Gate Read

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Trade-count cells | 3/9 | 9/9 | FAIL |
| Max zero-trade months | 4 | <= 3 | FAIL |
| Cross-broker persistence | Capital sub-threshold positive; Pepperstone/Dukascopy negative | Broadly positive above threshold | FAIL |

## Decision

Reject v0 and do not proceed to deciles, multisymbol, intrabar, or Gate 9 review. The Friday position-squaring premise is too sparse and does not produce cross-broker expectancy.
