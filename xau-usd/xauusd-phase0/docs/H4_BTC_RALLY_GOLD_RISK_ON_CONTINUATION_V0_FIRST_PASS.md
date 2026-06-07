# H4 BTC Rally Gold Risk-On Continuation v0 First Pass

Date: 2026-06-07

Expert: `h4_btc_rally_gold_risk_on_continuation_v0`

Hypothesis file: `docs/hypothesis_h4_btc_rally_gold_risk_on_continuation_v0.md`

SHA256: `a8a827aff2c9d98e7e9318e3ecea5dfe94d7d609accbc0b74adb3eb475b42dae`

## Verdict

REJECTED_FIRST_PASS. Do not tune v0.

This candidate tested shifted BTC rally pressure as a risk-on catalyst for bearish XAU H4 continuation after a completed support break. It failed because every broker/cost cell was negative, no PF cell reached threshold, trade counts were far below the minimum, and concentration was unusable.

## Smoke

PASS.

- Signals: 1
- Phase 0 result run allowed: false

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | Return % | Max DD % | Max zero months | Concentration |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 13 | 0.9378 | -0.1811 | 1.0350 | 14 | 100.00 |
| 2 | capital_com | median | 13 | 0.9378 | -0.1811 | 1.0350 | 14 | 100.00 |
| 3 | capital_com | p95 | 13 | 0.9245 | -0.2215 | 1.0452 | 14 | 100.00 |
| 4 | pepperstone | best_case | 17 | 0.3099 | -2.9978 | 3.1273 | 7 | 100.00 |
| 5 | pepperstone | median | 17 | 0.3099 | -2.9978 | 3.1273 | 7 | 100.00 |
| 6 | pepperstone | p95 | 17 | 0.3064 | -3.0282 | 3.1545 | 7 | 100.00 |
| 7 | dukascopy | best_case | 8 | 0.2808 | -1.6536 | 1.8379 | 10 | 100.00 |
| 8 | dukascopy | median | 8 | 0.2768 | -1.6240 | 1.7848 | 10 | 100.00 |
| 9 | dukascopy | p95 | 8 | 0.2633 | -1.6872 | 1.8285 | 10 | 100.00 |

## Gate Read

- PF >= 1.30 cells: 0/9
- Trade-count cells: 0/9
- Positive broker windows: 0/3
- Max zero-trade months: 14
- Concentration: failed; sparse samples were fully top-trade dominated

## Decision

Reject without tuning. This closes the BTC rally / risk-on continuation quadrant for the current shifted Yahoo daily BTC proxy. Combined with the failed BTC crash safe-haven continuation and rejected BTC stress-reversal variants, BTC daily OHLCV alone is not producing a worthy EA in the current Phase0 matrix.
