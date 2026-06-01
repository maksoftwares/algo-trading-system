# H4 XLP/XLY Consumer Rotation Reversal v0 First-Pass Result

Expert: `h4_xlp_xly_consumer_rotation_reversal_v0`
Hypothesis: `docs/hypothesis_h4_xlp_xly_consumer_rotation_reversal_v0.md`
Hypothesis SHA256: `e73bce2baa98f548c63ae3e8debd78322a93ba14ac8f5b9a158374dc9272a94a`
Status: `REJECTED_FIRST_PASS`

## Summary

`h4_xlp_xly_consumer_rotation_reversal_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. The candidate tested whether shifted public XLP/XLY consumer defensive-versus-discretionary rotation can identify H4 XAU reversal opportunities after a completed rejection candle.

The candidate is rejected first-pass. It produced enough trades in every cell, but it failed expectancy: 0/9 cells reached PF >= 1.30. Capital.com and Pepperstone were negative across all cost cases, while the only positive pocket was Dukascopy below threshold.

## Gate Snapshot

| Metric | Observed | Required | Result |
|---|---:|---:|---|
| Total cost-cell trades | 444 | n/a | Review only |
| Trade-count cells | 9/9 | 7/9 | PASS |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Positive-PnL cells | 3/9 | n/a | Weak |
| Best PF | 1.1214 | >= 1.30 | FAIL |
| Max zero-trade months | 3 | <= 3 | PASS |
| Largest single trade concentration | 60.6%-100.0% | <= 10% | FAIL |
| Top-5 trade concentration | 100.0%-420.3% | <= 40% | FAIL |

## Cell Results

| Cell | Broker | Cost | Trades | PF | Total PnL % | Win Rate | Max Zero Months |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | Capital.com | best_case | 44 | 0.7813 | -2.45% | 40.91% | 2 |
| 2 | Capital.com | median | 44 | 0.7813 | -2.45% | 40.91% | 2 |
| 3 | Capital.com | p95 | 44 | 0.7741 | -2.53% | 40.91% | 2 |
| 4 | Pepperstone | best_case | 58 | 0.5816 | -6.00% | 36.21% | 3 |
| 5 | Pepperstone | median | 58 | 0.5816 | -6.00% | 36.21% | 3 |
| 6 | Pepperstone | p95 | 58 | 0.5758 | -6.05% | 34.48% | 3 |
| 7 | Dukascopy | best_case | 46 | 1.1214 | 1.25% | 45.65% | 3 |
| 8 | Dukascopy | median | 46 | 1.1062 | 1.10% | 45.65% | 3 |
| 9 | Dukascopy | p95 | 46 | 1.0828 | 0.86% | 45.65% | 3 |

## Decision

Reject v0. Do not tune this candidate in place. The weak Dukascopy pocket is not enough to count as an independent higher-timeframe EA.
