# H1 Real-Yield Inflation Mix Reversal v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_real_yield_inflation_mix_reversal_v0` without tuning.

This candidate tested whether shifted 10-year real-yield declines paired with rising breakeven inflation, or the opposite hostile mix, can identify H1 gold reversal opportunities after a local spot move. It passed the trade-count floor in all cells, but failed PF persistence with 0/9 cells above 1.30 and only a Dukascopy-only positive pocket below threshold.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 43 | 30.23% | 0.5572 | -6.32% | 8.38% | 3 | FAIL |
| 2 | capital_com | median | 43 | 30.23% | 0.5572 | -6.32% | 8.38% | 3 | FAIL |
| 3 | capital_com | p95 | 43 | 30.23% | 0.5432 | -6.56% | 8.57% | 3 | FAIL |
| 4 | pepperstone | best_case | 50 | 34.00% | 0.7248 | -4.27% | 6.01% | 2 | FAIL |
| 5 | pepperstone | median | 50 | 34.00% | 0.7248 | -4.27% | 6.01% | 2 | FAIL |
| 6 | pepperstone | p95 | 50 | 34.00% | 0.7200 | -4.34% | 6.04% | 2 | FAIL |
| 7 | dukascopy | best_case | 43 | 44.19% | 1.2087 | +2.21% | 2.23% | 4 | FAIL |
| 8 | dukascopy | median | 43 | 44.19% | 1.1903 | +2.03% | 2.30% | 4 | FAIL |
| 9 | dukascopy | p95 | 43 | 44.19% | 1.1390 | +1.48% | 2.45% | 4 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 408 | Informational | PASS |
| Max zero-trade months | 4 | <= 3 | FAIL |
| Cross-broker persistence | Dukascopy-only positive pocket | Robust across windows | FAIL |
| Best observed PF | 1.2087 | >= 1.30 in most cells | FAIL |

## Interpretation

The real-yield plus breakeven-inflation mix is mechanically plausible, but this first-pass version did not produce a robust independent EA. The signal was negative in Capital.com and Pepperstone, and the only positive window stayed below threshold after costs. Because the hypothesis was locked before the run, the correct action is rejection rather than threshold adjustment.

## Next Action

Do not tune v0. A future macro lane should require either higher-frequency rate/real-yield data, event-surprise magnitudes, options-skew data, or a materially new mechanism instead of another daily-FRED threshold mix.
