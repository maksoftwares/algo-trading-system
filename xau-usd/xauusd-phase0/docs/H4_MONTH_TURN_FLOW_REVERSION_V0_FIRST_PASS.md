# H4 Month-Turn Flow Reversion v0 First-Pass Result

Expert: `h4_month_turn_flow_reversion_v0`
Hypothesis: `docs/hypothesis_h4_month_turn_flow_reversion_v0.md`
Hypothesis SHA256: `72a3078605a7010fea9301ee92f0adb44dfd86b15a6925b150654446b1ba4a93`
Status: `REJECTED_FIRST_PASS`

## Summary

`h4_month_turn_flow_reversion_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. The candidate tested whether month-end and month-start flow pressure on XAUUSD reverses after a completed H4 rejection candle.

The candidate is rejected first-pass. It produced enough trades in every cell, but it failed expectancy: 0/9 cells reached PF >= 1.30. Only the Capital.com 2016-2018 window was slightly positive, while Pepperstone 2019-2021 and Dukascopy 2022-2024 were negative across cost cases.

## Gate Snapshot

| Metric | Observed | Required | Result |
|---|---:|---:|---|
| Total cost-cell trades | 528 | n/a | Review only |
| Trade-count cells | 9/9 | 7/9 | PASS |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Positive-PnL cells | 3/9 | n/a | Weak |
| Best PF | 1.0286 | >= 1.30 | FAIL |
| Max zero-trade months | 2 | <= 3 | PASS |
| Largest single trade concentration | 100.0%-200.2% in negative/weak cells | <= 10% | FAIL |
| Top-5 trade concentration | 100.0%-981.5% in negative/weak cells | <= 40% | FAIL |

## Cell Results

| Cell | Broker | Cost | Trades | PF | Total PnL % | Win Rate | Max Zero Months |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | Capital.com | best_case | 59 | 1.0286 | 0.45% | 42.37% | 1 |
| 2 | Capital.com | median | 59 | 1.0286 | 0.45% | 42.37% | 1 |
| 3 | Capital.com | p95 | 59 | 1.0229 | 0.36% | 42.37% | 1 |
| 4 | Pepperstone | best_case | 62 | 0.7980 | -3.51% | 37.10% | 2 |
| 5 | Pepperstone | median | 62 | 0.7980 | -3.51% | 37.10% | 2 |
| 6 | Pepperstone | p95 | 62 | 0.7920 | -3.63% | 37.10% | 2 |
| 7 | Dukascopy | best_case | 55 | 0.8649 | -1.97% | 38.18% | 2 |
| 8 | Dukascopy | median | 55 | 0.8548 | -2.10% | 38.18% | 2 |
| 9 | Dukascopy | p95 | 55 | 0.8428 | -2.28% | 38.18% | 2 |

## Decision

Reject v0. Do not tune this candidate in place. Any future month-turn research must be a new hypothesis version with a different ex-ante mechanism or materially different independent data source.
