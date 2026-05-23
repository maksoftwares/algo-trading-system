# D1 Inside-Day Breakout v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`

`d1_inside_day_breakout_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell matrix without tuning. It is rejected because it failed multi-cell PF survival and failed the minimum trade-count gate in six of nine cells.

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | Return % | Max DD % | Gate 1 | Trade Count |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | capital_com | best_case | 41 | 1.690 | 6.06 | 1.71 | PASS | PASS |
| 2 | capital_com | median | 41 | 1.690 | 6.06 | 1.71 | PASS | PASS |
| 3 | capital_com | p95 | 41 | 1.678 | 5.98 | 1.72 | PASS | PASS |
| 4 | pepperstone | best_case | 11 | 0.826 | -0.51 | 0.87 | FAIL | FAIL |
| 5 | pepperstone | median | 11 | 0.826 | -0.51 | 0.87 | FAIL | FAIL |
| 6 | pepperstone | p95 | 11 | 0.823 | -0.52 | 0.87 | FAIL | FAIL |
| 7 | dukascopy | best_case | 12 | 0.730 | -0.85 | 2.31 | FAIL | FAIL |
| 8 | dukascopy | median | 12 | 0.728 | -0.86 | 2.32 | FAIL | FAIL |
| 9 | dukascopy | p95 | 12 | 0.723 | -0.88 | 2.33 | FAIL | FAIL |

Observed PF cells >= 1.30: `3/9`.

Observed cells with at least 40 trades: `3/9`.

## Decision

Reject v0 and do not tune it. The 2016-2018 Capital.com cell family was positive, but the later broker/windows had too few trades and negative expectancy. This is not an approved EA and should not proceed to deciles, multisymbol, or Gate 9.

## Artifacts

- Hypothesis: `docs/hypothesis_d1_inside_day_breakout_v0.md`
- Registration: `outputs/reports/d1_inside_day_breakout_v0_research_hypothesis_registration.md`
- Smoke report: `outputs/reports/d1_inside_day_breakout_v0_research_smoke.md`
- Matrix folder: `outputs/matrix_results/d1_inside_day_breakout_v0/`
