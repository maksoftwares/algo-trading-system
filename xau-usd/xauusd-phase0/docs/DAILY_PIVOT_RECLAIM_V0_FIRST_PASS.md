# Daily Pivot Reclaim v0 First-Pass Result

Date: 2026-05-23

## Verdict

`daily_pivot_reclaim_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated enough trades in every matrix cell, but it failed the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30. The only profitable cells were the Pepperstone best/median/P95 cells, and all remained below the required PF threshold.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 486 to 558 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 486 | 0.829 | -22.276 | 25.984 | 39.30% |
| 2 | capital_com | median | 486 | 0.829 | -22.276 | 25.984 | 39.30% |
| 3 | capital_com | p95 | 486 | 0.784 | -27.658 | 30.138 | 39.30% |
| 4 | pepperstone | best_case | 527 | 1.093 | 14.627 | 12.912 | 43.45% |
| 5 | pepperstone | median | 527 | 1.093 | 14.627 | 12.912 | 43.45% |
| 6 | pepperstone | p95 | 527 | 1.042 | 6.349 | 13.624 | 43.45% |
| 7 | dukascopy | best_case | 558 | 0.872 | -19.017 | 21.707 | 37.99% |
| 8 | dukascopy | median | 558 | 0.838 | -23.418 | 25.346 | 37.99% |
| 9 | dukascopy | p95 | 558 | 0.768 | -31.837 | 32.517 | 37.99% |

## Decision

Do not proceed to decile, multisymbol, adversarial, intrabar, or Phase 1 planning for this v0 candidate.

Do not tune `daily_pivot_reclaim_v0` in place. Any future daily-pivot or prior-session reference idea must use a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
