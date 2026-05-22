# Previous Day Extreme Retest v0 First-Pass Result

Date: 2026-05-22

## Verdict

`previous_day_extreme_retest_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated sufficient trade count, but it did not satisfy the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 478 to 704 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 583 | 0.876 | -18.619 | 27.581 | 42.02% |
| 2 | capital_com | median | 583 | 0.876 | -18.619 | 27.581 | 42.02% |
| 3 | capital_com | p95 | 583 | 0.817 | -26.861 | 31.369 | 42.02% |
| 4 | pepperstone | best_case | 478 | 0.967 | -4.760 | 24.857 | 40.38% |
| 5 | pepperstone | median | 478 | 0.967 | -4.760 | 24.857 | 40.38% |
| 6 | pepperstone | p95 | 478 | 0.919 | -11.364 | 26.980 | 40.38% |
| 7 | dukascopy | best_case | 704 | 1.060 | 12.973 | 12.931 | 42.90% |
| 8 | dukascopy | median | 704 | 1.006 | 1.186 | 14.447 | 42.90% |
| 9 | dukascopy | p95 | 704 | 0.902 | -18.025 | 21.358 | 42.76% |

## Decision

Do not proceed to decile, multisymbol, adversarial, or Phase 1 planning for this v0 candidate.

Do not tune `previous_day_extreme_retest_v0` in place. Any future previous-day-level idea must be a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
