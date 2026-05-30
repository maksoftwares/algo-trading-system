# H1 Credit Spread Shock Reversal v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_credit_spread_shock_reversal_v0` without tuning.

This candidate solved sample size in all 9 cells, but no cell reached PF >= 1.30. Dukascopy showed a small positive pocket at best/median costs, Capital.com and Pepperstone were negative, and P95 cost erased the Dukascopy edge.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 103 | 28.16% | 0.5082 | -16.09% | 17.53% | 2 | FAIL |
| 2 | capital_com | median | 103 | 28.16% | 0.5082 | -16.09% | 17.53% | 2 | FAIL |
| 3 | capital_com | p95 | 103 | 28.16% | 0.4989 | -16.46% | 17.84% | 2 | FAIL |
| 4 | pepperstone | best_case | 119 | 36.97% | 0.8449 | -5.45% | 9.88% | 3 | FAIL |
| 5 | pepperstone | median | 119 | 36.97% | 0.8449 | -5.45% | 9.88% | 3 | FAIL |
| 6 | pepperstone | p95 | 119 | 36.97% | 0.8316 | -5.93% | 10.07% | 3 | FAIL |
| 7 | dukascopy | best_case | 112 | 41.07% | 1.0278 | +0.83% | 5.36% | 3 | FAIL |
| 8 | dukascopy | median | 112 | 41.07% | 1.0158 | +0.47% | 5.41% | 3 | FAIL |
| 9 | dukascopy | p95 | 112 | 41.07% | 0.9681 | -0.95% | 6.19% | 3 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 1,002 | Informational | PASS |
| Max zero-trade months | 3 | <= 3 | PASS |
| Cross-broker persistence | Dukascopy-only positive pocket below threshold | Robust across windows | FAIL |
| Best observed PF | 1.0278 | >= 1.30 in most cells | FAIL |

## Interpretation

Shifted FRED BAA10Y/AAA10Y corporate-credit shocks did not create a robust tradable H1 XAU reversal edge. This confirms that corporate credit spread stress has now been tested in both H4 momentum and H1 shock-reversal forms without producing an independent approved EA.

## Next Action

Do not tune this v0 candidate. Keep searching for a genuinely different data class or behavior family; primary COMEX/CME order-flow, futures volume, or options-skew data remains higher priority than another public daily macro proxy.
