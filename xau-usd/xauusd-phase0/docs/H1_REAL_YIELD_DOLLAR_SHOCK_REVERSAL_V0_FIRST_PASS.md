# H1 Real-Yield Dollar Shock Reversal v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`
Date: 2026-05-29
Expert: `h1_real_yield_dollar_shock_reversal_v0`
Hypothesis SHA256: `69574bf76727cbb2b306540863cbb3f3acceba1af6ceefb18315a0738ac83cee`

## Hypothesis

This candidate tested whether completed H1 XAUUSD reversal candles after a joint real-yield and broad-dollar shock could capture intraday overshoot reversal. It used shifted FRED `DFII10` real-yield data and shifted FRED `DTWEXBGS` broad-dollar data, so it is an independent macro/reversal attempt rather than a level/retest variant.

## Matrix Result

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 39 | 35.90% | 0.6056 | -4.58% | 4 | 5.97% |
| 2 | capital_com | median | 39 | 35.90% | 0.6056 | -4.58% | 4 | 5.97% |
| 3 | capital_com | p95 | 39 | 35.90% | 0.5822 | -4.90% | 4 | 6.26% |
| 4 | pepperstone | best_case | 44 | 47.73% | 1.1356 | 1.43% | 6 | 3.66% |
| 5 | pepperstone | median | 44 | 47.73% | 1.1356 | 1.43% | 6 | 3.66% |
| 6 | pepperstone | p95 | 44 | 47.73% | 1.1295 | 1.36% | 6 | 3.64% |
| 7 | dukascopy | best_case | 86 | 41.86% | 0.9896 | -0.21% | 2 | 2.98% |
| 8 | dukascopy | median | 86 | 41.86% | 0.9637 | -0.74% | 2 | 3.26% |
| 9 | dukascopy | p95 | 86 | 41.86% | 0.9105 | -1.84% | 2 | 4.09% |

## Gate Summary

- PF cells >= 1.30: `0/9`, required `7/9`.
- Trade-count cells >= 40: `6/9`, required `9/9` for clean matrix viability.
- Total matrix trades across cost cells: `507`.
- Capital.com failed both PF and the 40-trade floor.
- Pepperstone had the best result but stayed below the PF threshold.
- Dukascopy was active enough but below breakeven after costs.

## Decision

Reject v0 without tuning. The macro shock/reversal idea had enough activity in two broker windows but did not show cross-broker expectancy. Do not loosen thresholds or revise this hypothesis in place. Any future real-yield/dollar idea must be a new version with a new pre-registration and a clear reason why it is mechanically different from this failed H1 reversal attempt.
