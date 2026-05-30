# H1 HG/GC Copper-Gold Rotation Reversal v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_hg_gc_copper_gold_rotation_reversal_v0` without tuning.

This candidate tested whether shifted direct copper futures versus gold futures pressure marks H1 XAUUSD overextension after local XAU has already moved with the copper/gold pressure and then prints a rejection candle. It solved sample size across all broker/cost cells, but failed PF persistence with only 1/9 cells above 1.30 and max zero-trade months above the activity threshold.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 55 | 38.18% | 0.5512 | -7.11% | 8.97% | 1 | FAIL |
| 2 | capital_com | median | 55 | 38.18% | 0.5512 | -7.11% | 8.97% | 1 | FAIL |
| 3 | capital_com | p95 | 55 | 38.18% | 0.5396 | -7.31% | 9.13% | 1 | FAIL |
| 4 | pepperstone | best_case | 44 | 38.64% | 0.7877 | -2.52% | 4.56% | 4 | FAIL |
| 5 | pepperstone | median | 44 | 38.64% | 0.7877 | -2.52% | 4.56% | 4 | FAIL |
| 6 | pepperstone | p95 | 44 | 38.64% | 0.7780 | -2.64% | 4.60% | 4 | FAIL |
| 7 | dukascopy | best_case | 74 | 50.00% | 1.3188 | +4.92% | 2.85% | 2 | PASS_PF_ONLY |
| 8 | dukascopy | median | 74 | 50.00% | 1.2700 | +4.17% | 2.87% | 2 | FAIL |
| 9 | dukascopy | p95 | 74 | 48.65% | 1.2121 | +3.28% | 2.89% | 2 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 1/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 519 | Informational | PASS |
| Max zero-trade months | 4 | <= 3 | FAIL |
| Cross-broker persistence | Dukascopy-only pocket; Capital.com and Pepperstone negative | Robust positive edge | FAIL |
| Best observed PF | 1.3188 | >= 1.30 in most cells | FAIL |

## Interpretation

The paired reversal expression did not rescue the direct HG/GC data class. Dukascopy showed one best-case PF pocket, but it weakened under higher costs and did not transfer to Capital.com or Pepperstone. Activity was adequate, but edge persistence was not.

## Next Action

Do not tune v0. Treat direct copper/gold rotation reversal as rejected under the current H1 expression. A future revisit would need materially better intraday futures/order-flow/options data, not threshold edits to this v0.
