# H1 Real-Yield Dollar Shock Follow-Through v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`
Date: 2026-05-29
Expert: `h1_real_yield_dollar_shock_followthrough_v0`
Hypothesis SHA256: `cbc87b357875b8c28ec63e7827b6e26b22349814f1e86bcc06d480597bd6a623`

## Hypothesis

This candidate tested whether completed H1 XAUUSD continuation candles after a joint real-yield and broad-dollar shock could capture intraday macro-pressure follow-through. It used shifted FRED `DFII10` real-yield data and shifted FRED `DTWEXBGS` broad-dollar data.

## Matrix Result

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 49 | 42.86% | 1.1400 | 1.76% | 3 | 3.35% |
| 2 | capital_com | median | 49 | 42.86% | 1.1400 | 1.76% | 3 | 3.35% |
| 3 | capital_com | p95 | 49 | 42.86% | 1.1118 | 1.41% | 3 | 3.41% |
| 4 | pepperstone | best_case | 31 | 45.16% | 1.3696 | 2.32% | 8 | 1.94% |
| 5 | pepperstone | median | 31 | 45.16% | 1.3696 | 2.32% | 8 | 1.94% |
| 6 | pepperstone | p95 | 31 | 45.16% | 1.3560 | 2.25% | 8 | 1.95% |
| 7 | dukascopy | best_case | 78 | 39.74% | 0.9065 | -1.93% | 2 | 3.90% |
| 8 | dukascopy | median | 78 | 39.74% | 0.8862 | -2.36% | 2 | 4.10% |
| 9 | dukascopy | p95 | 78 | 38.46% | 0.8442 | -3.24% | 2 | 4.73% |

## Gate Summary

- PF cells >= 1.30: `3/9`, required `7/9`.
- Trade-count cells >= 40: `6/9`.
- Total matrix trades across cost cells: `474`.
- Passing PF cells were Pepperstone-only and below the trade-count floor.
- Capital.com was mildly positive but below threshold.
- Dukascopy was negative across all cost cases.

## Decision

Reject v0 without tuning. The follow-through version showed a Pepperstone pocket but not a cross-broker macro edge. Because both the H1 real-yield/dollar reversal and follow-through variants failed, this current-data macro shock lane is closed unless a future version adds a genuinely new data source or mechanical reason.
