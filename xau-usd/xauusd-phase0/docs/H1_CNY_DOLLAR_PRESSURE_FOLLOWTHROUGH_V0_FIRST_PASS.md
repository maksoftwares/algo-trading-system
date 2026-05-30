# H1 CNY-Dollar Pressure Follow-Through v0 First Pass

Status: REJECTED_FIRST_PASS
Hypothesis: `docs/hypothesis_h1_cny_dollar_pressure_followthrough_v0.md`
Research hash: `d3415e70b40650b43c84f76f1ee301aabfff3fc7c6d3e8e17602a8d904cab0c7`
Data proxy: `data/raw/macro/FRED_DEXCHUS.csv`
Data source: FRED `DEXCHUS` official yuan-per-dollar daily series plus existing FRED `DTWEXBGS` broad-dollar series

## Decision

Reject v0 without tuning.

This candidate unblocked the prior CYB/UUP yuan-dollar lane by replacing the stale ETF proxy with an official FRED CNY-dollar pressure input. It produced enough sample size in every matrix cell, but failed the hard first-pass expectancy gate with 0/9 PF cells >= 1.30. Capital.com and Pepperstone were positive but below threshold; Dukascopy was negative across all cost settings.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Capital.com | best | 153 | 47.71% | 1.2925 | +11.51% | 4.18% | 1 | FAIL |
| 2 | Capital.com | median | 153 | 47.71% | 1.2925 | +11.51% | 4.18% | 1 | FAIL |
| 3 | Capital.com | p95 | 153 | 47.71% | 1.2605 | +10.31% | 4.28% | 1 | FAIL |
| 4 | Pepperstone | best | 111 | 45.05% | 1.1991 | +5.73% | 4.14% | 1 | FAIL |
| 5 | Pepperstone | median | 111 | 45.05% | 1.1991 | +5.73% | 4.14% | 1 | FAIL |
| 6 | Pepperstone | p95 | 111 | 45.05% | 1.1789 | +5.15% | 4.12% | 1 | FAIL |
| 7 | Dukascopy | best | 132 | 40.91% | 0.9220 | -2.80% | 12.97% | 3 | FAIL |
| 8 | Dukascopy | median | 132 | 40.15% | 0.9021 | -3.51% | 13.31% | 3 | FAIL |
| 9 | Dukascopy | p95 | 132 | 39.39% | 0.8634 | -4.86% | 13.98% | 3 | FAIL |

## Gate Read

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| Matrix PF cells | 0/9 | >= 7/9 | FAIL |
| Trade-count cells | 9/9 | 9/9 with >= 40 trades | PASS |
| Total matrix trades | 1,188 | Informational | PASS |
| Max zero-trade months | 3 | <= 3 | PASS |
| Cross-broker portability | Capital.com/Pepperstone positive but below threshold; Dukascopy negative | Robust across windows | FAIL |
| Cost sensitivity | P95 weakens sub-threshold cells | P95 should not break the edge | FAIL |
| Concentration | Dukascopy positive-PnL contribution is not robust because total PnL is negative | No fragile positive-pocket dependency | FAIL |

## Interpretation

The official CNY-dollar pressure data class is better behaved than the stale CYB/UUP ETF proxy from a coverage standpoint, but the actual XAU follow-through edge is too weak and broker-dependent. The best observed PF is 1.2925, just below the 1.30 threshold, and the losing Dukascopy window prevents this from being treated as a near miss.

## Next Action

Do not tune this v0 candidate. Continue the independent search in a different mechanism or a materially higher-quality data class. This result does not alter approved/provisional EA status, Phase 1 dry-run permissions, Phase 2 readiness, or demo observer authority.
