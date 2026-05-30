# Weekend Gap Reversion v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `weekend_gap_reversion_v0` without tuning.

This candidate tested whether the first completed M15 candle after a weekend-style market break could fade a sufficiently large XAUUSD opening gap back toward the pre-gap close. It failed sample-size, PF persistence, activity, and cross-broker transfer.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 11 | 27.27% | 0.5933 | -1.60% | 2.39% | 11 | FAIL |
| 2 | capital_com | median | 11 | 27.27% | 0.5933 | -1.60% | 2.39% | 11 | FAIL |
| 3 | capital_com | p95 | 11 | 27.27% | 0.5747 | -1.69% | 2.47% | 11 | FAIL |
| 4 | pepperstone | best_case | 0 | 0.00% | 0.0000 | +0.00% | 0.00% | 36 | FAIL |
| 5 | pepperstone | median | 0 | 0.00% | 0.0000 | +0.00% | 0.00% | 36 | FAIL |
| 6 | pepperstone | p95 | 0 | 0.00% | 0.0000 | +0.00% | 0.00% | 36 | FAIL |
| 7 | dukascopy | best_case | 0 | 0.00% | 0.0000 | +0.00% | 0.00% | 36 | FAIL |
| 8 | dukascopy | median | 0 | 0.00% | 0.0000 | +0.00% | 0.00% | 36 | FAIL |
| 9 | dukascopy | p95 | 0 | 0.00% | 0.0000 | +0.00% | 0.00% | 36 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 0/9 | 9/9 | FAIL |
| Total matrix trades | 33 | Informational | PASS |
| Max zero-trade months | 36 | <= 3 | FAIL |
| Cross-broker persistence | Capital.com sparse negative; Pepperstone/Dukascopy no qualifying trades | Robust positive edge | FAIL |
| Best observed PF | 0.5933 | >= 1.30 in most cells | FAIL |

## Interpretation

The weekend-gap setup is too sparse in the current broker-normalized data and the only result-producing broker slice is negative. It does not provide an independent diversification candidate.

## Next Action

Do not tune v0. Treat this calendar/microstructure gap-reversion lane as rejected unless a future review introduces a materially different data class or venue-specific gap dataset.
