# H1 TIP/IEF Real-Yield Rotation Follow-Through v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`
Date: 2026-05-29
Expert: `h1_tip_ief_real_yield_rotation_followthrough_v0`
Hypothesis SHA256: `a94731488566957c1a5733a3b0dc3ab43fb35179a0fc1cba527cdc038aaa12fd`

## Hypothesis

This candidate tested whether XAUUSD follows a traded inflation-protected versus nominal Treasury proxy built from shifted daily TIP and IEF ETF observations, after H1 XAU price confirms in the same direction.

## Matrix Result

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 88 | 42.05% | 0.9390 | -1.41% | 4 | 5.61% |
| 2 | capital_com | median | 88 | 42.05% | 0.9390 | -1.41% | 4 | 5.61% |
| 3 | capital_com | p95 | 88 | 42.05% | 0.9158 | -1.95% | 4 | 5.78% |
| 4 | pepperstone | best_case | 145 | 44.83% | 1.1813 | 6.75% | 1 | 3.93% |
| 5 | pepperstone | median | 145 | 44.83% | 1.1813 | 6.75% | 1 | 3.93% |
| 6 | pepperstone | p95 | 145 | 44.83% | 1.1649 | 6.13% | 1 | 3.86% |
| 7 | dukascopy | best_case | 127 | 37.01% | 0.8108 | -6.46% | 2 | 8.87% |
| 8 | dukascopy | median | 127 | 37.01% | 0.7971 | -6.89% | 2 | 9.22% |
| 9 | dukascopy | p95 | 127 | 37.01% | 0.7645 | -7.97% | 2 | 10.16% |

## Gate Summary

- PF cells >= 1.30: `0/9`, required `7/9`.
- Trade-count cells >= 40: `9/9`.
- Total matrix trades across cost cells: `1,080`.
- Pepperstone was positive but below threshold.
- Capital.com and Dukascopy were negative across all cost cases.

## Decision

Reject v0 without tuning. The TIP/IEF real-yield rotation data class produced adequate sample size, but it did not produce cross-broker edge persistence and failed the core PF gate.
