# H1 Real-Yield Inflation Mix Follow-Through v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_real_yield_inflation_mix_followthrough_v0` without tuning.

This candidate tested whether shifted 10-year real-yield and breakeven-inflation mix conditions have direct H1 follow-through value after spot starts moving in the same direction. It passed the trade-count floor in all cells, but failed PF persistence with 0/9 cells above 1.30. Pepperstone had a positive pocket below threshold, while Capital.com and Dukascopy were negative.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 53 | 35.85% | 0.6654 | -5.35% | 5.55% | 2 | FAIL |
| 2 | capital_com | median | 53 | 35.85% | 0.6654 | -5.35% | 5.55% | 2 | FAIL |
| 3 | capital_com | p95 | 53 | 35.85% | 0.6521 | -5.59% | 5.80% | 2 | FAIL |
| 4 | pepperstone | best_case | 88 | 46.59% | 1.1544 | +3.40% | 3.55% | 2 | FAIL |
| 5 | pepperstone | median | 88 | 46.59% | 1.1544 | +3.40% | 3.55% | 2 | FAIL |
| 6 | pepperstone | p95 | 88 | 46.59% | 1.1279 | +2.83% | 3.66% | 2 | FAIL |
| 7 | dukascopy | best_case | 112 | 41.07% | 0.8788 | -3.73% | 7.32% | 1 | FAIL |
| 8 | dukascopy | median | 112 | 40.18% | 0.8565 | -4.39% | 7.87% | 1 | FAIL |
| 9 | dukascopy | p95 | 112 | 40.18% | 0.8133 | -5.69% | 8.90% | 1 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 759 | Informational | PASS |
| Max zero-trade months | 2 | <= 3 | PASS |
| Cross-broker persistence | Pepperstone-only positive pocket | Robust across windows | FAIL |
| Best observed PF | 1.1544 | >= 1.30 in most cells | FAIL |

## Interpretation

The paired follow-through hypothesis produced more activity than the reversal version and solved the activity gate, but it did not reveal a robust independent edge. The best pocket stayed below the PF threshold and failed to generalize across broker windows.

## Next Action

Do not tune v0. The real-yield / breakeven-inflation data class has now failed both reversal and follow-through H1 expressions. A future macro effort should require a genuinely new input, such as intraday rates, event surprise values, or options skew.
