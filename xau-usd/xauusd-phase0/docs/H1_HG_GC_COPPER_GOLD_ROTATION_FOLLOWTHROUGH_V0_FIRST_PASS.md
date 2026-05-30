# H1 HG/GC Copper-Gold Rotation Follow-Through v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_hg_gc_copper_gold_rotation_followthrough_v0` without tuning.

This candidate tested whether shifted direct copper futures versus gold futures pressure supports H1 XAUUSD follow-through after local XAU direction has already aligned with the copper/gold rotation. It solved sample size across all broker/cost cells, but failed PF persistence with 0/9 cells above 1.30.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 96 | 38.54% | 0.8473 | -4.18% | 8.05% | 1 | FAIL |
| 2 | capital_com | median | 96 | 38.54% | 0.8473 | -4.18% | 8.05% | 1 | FAIL |
| 3 | capital_com | p95 | 96 | 38.54% | 0.8234 | -4.85% | 8.54% | 1 | FAIL |
| 4 | pepperstone | best_case | 95 | 44.21% | 1.1018 | +2.43% | 3.28% | 1 | FAIL |
| 5 | pepperstone | median | 95 | 44.21% | 1.1018 | +2.43% | 3.28% | 1 | FAIL |
| 6 | pepperstone | p95 | 95 | 44.21% | 1.0693 | +1.66% | 3.45% | 1 | FAIL |
| 7 | dukascopy | best_case | 127 | 33.86% | 0.7154 | -10.10% | 13.55% | 1 | FAIL |
| 8 | dukascopy | median | 127 | 33.86% | 0.7033 | -10.58% | 13.86% | 1 | FAIL |
| 9 | dukascopy | p95 | 127 | 33.07% | 0.6657 | -11.91% | 14.59% | 1 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 954 | Informational | PASS |
| Max zero-trade months | 1 | <= 3 | PASS |
| Cross-broker persistence | Pepperstone positive below threshold; Capital.com/Dukascopy negative | Robust positive edge | FAIL |
| Best observed PF | 1.1018 | >= 1.30 in most cells | FAIL |

## Interpretation

The direct HG/GC futures rotation data class is useful to have tested because it is closer to primary futures-relative pressure than the prior DBB/UUP ETF basket. The first pass still does not show an edge: the Pepperstone pocket was below threshold and did not transfer to Capital.com or Dukascopy.

## Next Action

Do not tune v0. Treat direct copper/gold rotation as rejected under the current H1 follow-through expression. A future revisit would need a materially different data class, such as intraday futures spreads, order flow, or options skew, not a threshold edit to this v0.
