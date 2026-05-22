# Weekly Level Reclaim v0 First-Pass Result

Date: 2026-05-22

## Verdict

`weekly_level_reclaim_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated sufficient trade count, but it did not satisfy the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 113 to 129 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 119 | 0.788 | -7.511 | 8.982 | 37.82% |
| 2 | capital_com | median | 119 | 0.788 | -7.511 | 8.982 | 37.82% |
| 3 | capital_com | p95 | 119 | 0.751 | -8.906 | 10.266 | 37.82% |
| 4 | pepperstone | best_case | 113 | 0.992 | -0.256 | 6.065 | 40.71% |
| 5 | pepperstone | median | 113 | 0.992 | -0.256 | 6.065 | 40.71% |
| 6 | pepperstone | p95 | 113 | 0.959 | -1.308 | 6.360 | 40.71% |
| 7 | dukascopy | best_case | 129 | 0.880 | -4.712 | 9.329 | 37.98% |
| 8 | dukascopy | median | 129 | 0.847 | -5.937 | 9.637 | 37.98% |
| 9 | dukascopy | p95 | 129 | 0.777 | -8.576 | 10.414 | 37.98% |

## Decision

Do not proceed to decile, multisymbol, adversarial, or Phase 1 planning for this v0 candidate.

Do not tune `weekly_level_reclaim_v0` in place. Any future weekly-level idea must be a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
