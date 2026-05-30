# H1 Breakeven Inflation Shock Reversal v0 First Pass

Generated: 2026-05-30
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h1_breakeven_inflation_shock_reversal_v0` without tuning.

This candidate solved sample size but failed the main matrix gate. All 9 cells reached at least 40 trades, but no cell reached PF >= 1.30. Every broker/cost window was negative after costs.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 87 | 32.18% | 0.6714 | -8.78% | 10.93% | 2 | FAIL |
| 2 | capital_com | median | 87 | 32.18% | 0.6714 | -8.78% | 10.93% | 2 | FAIL |
| 3 | capital_com | p95 | 87 | 32.18% | 0.6521 | -9.34% | 11.39% | 2 | FAIL |
| 4 | pepperstone | best_case | 116 | 37.07% | 0.7948 | -6.79% | 7.13% | 0 | FAIL |
| 5 | pepperstone | median | 116 | 37.07% | 0.7948 | -6.79% | 7.13% | 0 | FAIL |
| 6 | pepperstone | p95 | 116 | 37.07% | 0.7829 | -7.17% | 7.49% | 0 | FAIL |
| 7 | dukascopy | best_case | 82 | 37.80% | 0.8992 | -2.35% | 7.48% | 1 | FAIL |
| 8 | dukascopy | median | 82 | 37.80% | 0.8736 | -2.94% | 7.73% | 1 | FAIL |
| 9 | dukascopy | p95 | 82 | 37.80% | 0.8120 | -4.38% | 8.36% | 1 | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 855 | Informational | PASS |
| Max zero-trade months | 2 | <= 3 | PASS |
| Cross-broker persistence | Every broker/cost window negative | Robust across windows | FAIL |
| Best observed PF | 0.8992 | >= 1.30 in most cells | FAIL |

## Interpretation

The shifted breakeven-inflation shock feature did not produce a tradable intraday XAU reversal edge. The result is cleaner than a borderline fail: sample size was adequate, but expectancy was negative across all cells.

## Next Action

Do not tune this v0 candidate. Treat breakeven inflation as tested in both H4 momentum and H1 shock-reversal forms, with no approved independent EA.
