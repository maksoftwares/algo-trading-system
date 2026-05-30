# H1 Financial Conditions Shock Reversal v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_financial_conditions_shock_reversal_v0` without tuning.

This candidate solved sample size in all 9 cells, but no cell reached PF >= 1.30. Pepperstone showed a small positive pocket below threshold, while Capital.com and Dukascopy were negative after costs. Activity also failed because max zero-trade months reached 6 in Dukascopy.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 132 | 40.91% | 0.9474 | -1.94% | 10.38% | 4 | FAIL |
| 2 | capital_com | median | 132 | 40.91% | 0.9474 | -1.94% | 10.38% | 4 | FAIL |
| 3 | capital_com | p95 | 132 | 40.91% | 0.9256 | -2.75% | 10.74% | 4 | FAIL |
| 4 | pepperstone | best_case | 169 | 42.60% | 1.0737 | +3.45% | 4.10% | 2 | FAIL |
| 5 | pepperstone | median | 169 | 42.60% | 1.0737 | +3.45% | 4.10% | 2 | FAIL |
| 6 | pepperstone | p95 | 169 | 42.60% | 1.0604 | +2.84% | 4.17% | 2 | FAIL |
| 7 | dukascopy | best_case | 127 | 38.58% | 0.9295 | -2.49% | 5.79% | 6 | FAIL |
| 8 | dukascopy | median | 127 | 38.58% | 0.9124 | -3.07% | 5.74% | 6 | FAIL |
| 9 | dukascopy | p95 | 127 | 38.58% | 0.8698 | -4.58% | 6.59% | 6 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 1,284 | Informational | PASS |
| Max zero-trade months | 6 | <= 3 | FAIL |
| Cross-broker persistence | Pepperstone-only positive pocket below threshold | Robust across windows | FAIL |
| Best observed PF | 1.0737 | >= 1.30 in most cells | FAIL |

## Interpretation

Shifted FRED NFCI/ANFCI financial-conditions shocks did not create a robust tradable H1 XAU reversal edge. This confirms that financial-conditions stress has now been tested in both H4 stress-reversal and H1 shock-reversal forms without producing an independent approved EA.

## Next Action

Do not tune this v0 candidate. Continue the independent EA hunt only with fresh, pre-registered hypotheses or a genuinely stronger data class.
