# H1 Session Impulse Reversion v0 First Pass

Status: REJECTED_FIRST_PASS
Date: 2026-05-29
Hypothesis SHA256: `019da38d3e405b4a2510de8e417e517a0c3f9f292770e39ea5222afe0d042e2d`

`h1_session_impulse_reversion_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. The candidate tested whether active-session H1 displacement away from EMA/ATR value creates an independent mean-reversion edge. It produced enough trades in every matrix cell, but it failed expectancy: 0/9 cells reached PF >= 1.30, Capital.com was strongly negative, and the only positive pocket was Pepperstone below the PF threshold.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best | 264 | 37.50% | 0.706 | -20.27% | 22.19% | 0 |
| 2 | Capital.com | median | 264 | 37.50% | 0.706 | -20.27% | 22.19% | 0 |
| 3 | Capital.com | p95 | 264 | 37.12% | 0.688 | -21.47% | 23.25% | 0 |
| 4 | Pepperstone | best | 254 | 49.21% | 1.264 | 16.52% | 9.53% | 0 |
| 5 | Pepperstone | median | 254 | 49.21% | 1.264 | 16.52% | 9.53% | 0 |
| 6 | Pepperstone | p95 | 254 | 49.21% | 1.239 | 14.96% | 9.97% | 0 |
| 7 | Dukascopy | best | 258 | 46.12% | 1.053 | 3.45% | 8.06% | 0 |
| 8 | Dukascopy | median | 258 | 46.12% | 1.026 | 1.69% | 8.06% | 0 |
| 9 | Dukascopy | p95 | 258 | 46.12% | 0.967 | -2.14% | 9.95% | 0 |

## Gate Read

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Trade-count cells | 9/9 | 9/9 | PASS |
| Max zero-trade months | 0 | <= 3 | PASS |
| Cross-broker persistence | Capital negative; Pepperstone positive but sub-threshold; Dukascopy marginal | Broadly positive above threshold | FAIL |

## Decision

Reject v0 and do not proceed to deciles, multisymbol, intrabar, or Gate 9 review. The active-session impulse-reversion mechanism does not create enough cross-broker edge and should not be tuned in place.
