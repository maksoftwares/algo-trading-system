# D1 Outside-Day Follow-Through v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`

`d1_outside_day_followthrough_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell matrix without tuning. It is rejected because every cell failed PF coverage and every cell failed the minimum trade-count gate.

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | Return % | Max DD % | Gate 1 | Trade Count |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | capital_com | best_case | 33 | 0.542 | -5.11 | 5.69 | FAIL | FAIL |
| 2 | capital_com | median | 33 | 0.542 | -5.11 | 5.69 | FAIL | FAIL |
| 3 | capital_com | p95 | 33 | 0.538 | -5.17 | 5.74 | FAIL | FAIL |
| 4 | pepperstone | best_case | 22 | 0.563 | -3.01 | 3.37 | FAIL | FAIL |
| 5 | pepperstone | median | 22 | 0.563 | -3.01 | 3.37 | FAIL | FAIL |
| 6 | pepperstone | p95 | 22 | 0.558 | -3.06 | 3.39 | FAIL | FAIL |
| 7 | dukascopy | best_case | 32 | 0.748 | -2.29 | 4.05 | FAIL | FAIL |
| 8 | dukascopy | median | 32 | 0.746 | -2.30 | 4.05 | FAIL | FAIL |
| 9 | dukascopy | p95 | 32 | 0.731 | -2.47 | 4.21 | FAIL | FAIL |

Observed PF cells >= 1.30: `0/9`.

Observed cells with at least 40 trades: `0/9`.

## Decision

Reject v0 and do not tune it. This is not an approved EA and should not proceed to deciles, multisymbol, or Gate 9.

## Artifacts

- Hypothesis: `docs/hypothesis_d1_outside_day_followthrough_v0.md`
- Registration: `outputs/reports/d1_outside_day_followthrough_v0_research_hypothesis_registration.md`
- Smoke report: `outputs/reports/d1_outside_day_followthrough_v0_research_smoke.md`
- Matrix folder: `outputs/matrix_results/d1_outside_day_followthrough_v0/`
