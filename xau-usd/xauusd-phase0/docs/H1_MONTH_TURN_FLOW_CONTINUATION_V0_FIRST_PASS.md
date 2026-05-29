# H1 Month-Turn Flow Continuation v0 First Pass

Status: REJECTED_FIRST_PASS
Date: 2026-05-29
Hypothesis SHA256: `e2d6e6db1cf028ea797f7a2277bd3b85597b4dcc1182fbd7bcb97720f9ea6ba8`

`h1_month_turn_flow_continuation_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. The candidate tested whether month-end/month-start flow pressure combined with H1 trend continuation can produce an independent, non-retest XAUUSD edge. It produced enough trades in every cell and had stable activity, but it failed first-pass expectancy: 0/9 cells reached PF >= 1.30 and Dukascopy was negative across all cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best | 167 | 47.31% | 1.206 | 9.42% | 8.87% | 0 |
| 2 | Capital.com | median | 167 | 47.31% | 1.206 | 9.42% | 8.87% | 0 |
| 3 | Capital.com | p95 | 167 | 47.31% | 1.175 | 8.00% | 9.23% | 0 |
| 4 | Pepperstone | best | 165 | 42.42% | 1.076 | 3.46% | 4.45% | 0 |
| 5 | Pepperstone | median | 165 | 42.42% | 1.076 | 3.46% | 4.45% | 0 |
| 6 | Pepperstone | p95 | 165 | 42.42% | 1.051 | 2.32% | 4.54% | 0 |
| 7 | Dukascopy | best | 176 | 36.93% | 0.839 | -7.92% | 11.41% | 0 |
| 8 | Dukascopy | median | 176 | 36.93% | 0.822 | -8.71% | 11.69% | 0 |
| 9 | Dukascopy | p95 | 176 | 36.36% | 0.778 | -10.80% | 12.65% | 0 |

## Gate Read

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Trade-count cells | 9/9 | 9/9 | PASS |
| Max zero-trade months | 0 | <= 3 | PASS |
| Cross-broker persistence | Capital/Pepperstone positive but sub-threshold; Dukascopy negative | Broadly positive above threshold | FAIL |

## Decision

Reject v0 and do not proceed to deciles, multisymbol, intrabar, or Gate 9 review. The month-turn timing idea created activity and some Capital.com/Pepperstone positive expectancy, but it did not produce cross-broker PF strength and should not be tuned in place.
