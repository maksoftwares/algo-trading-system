# Weekly Open Reversion v0 First-Pass Result

Status: `REJECTED_FIRST_PASS`

`weekly_open_reversion_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell matrix without tuning. It is rejected because it failed the primary PF coverage gate.

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | Return % | Max DD % | Gate 1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | capital_com | best_case | 209 | 0.610 | -29.07 | 29.22 | FAIL |
| 2 | capital_com | median | 209 | 0.610 | -29.07 | 29.22 | FAIL |
| 3 | capital_com | p95 | 209 | 0.589 | -30.73 | 30.82 | FAIL |
| 4 | pepperstone | best_case | 220 | 0.943 | -5.06 | 21.58 | FAIL |
| 5 | pepperstone | median | 220 | 0.943 | -5.06 | 21.58 | FAIL |
| 6 | pepperstone | p95 | 220 | 0.914 | -7.67 | 22.51 | FAIL |
| 7 | dukascopy | best_case | 197 | 1.175 | 13.39 | 9.63 | FAIL |
| 8 | dukascopy | median | 197 | 1.146 | 11.09 | 9.98 | FAIL |
| 9 | dukascopy | p95 | 197 | 1.094 | 7.06 | 11.22 | FAIL |

Observed PF cells >= 1.30: `0/9`.

## Decision

Reject v0 and do not tune it. The latest Dukascopy window was positive, but the first two broker/windows were negative and the candidate never reached the PF threshold in any cell. This is not an approved EA and should not proceed to deciles, multisymbol, or Gate 9.

## Artifacts

- Hypothesis: `docs/hypothesis_weekly_open_reversion_v0.md`
- Registration: `outputs/reports/weekly_open_reversion_v0_research_hypothesis_registration.md`
- Smoke report: `outputs/reports/weekly_open_reversion_v0_research_smoke.md`
- Matrix folder: `outputs/matrix_results/weekly_open_reversion_v0/`
