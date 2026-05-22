# Opening Drive Failed Continuation v0 First-Pass Result

Date: 2026-05-22

## Verdict

`opening_drive_failed_continuation_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated sufficient trade count in every matrix cell, but it did not satisfy the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30, and every cell had negative total return.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 221 to 294 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 221 | 0.791 | -13.498 | 15.601 | 38.01% |
| 2 | capital_com | median | 221 | 0.791 | -13.498 | 15.601 | 38.01% |
| 3 | capital_com | p95 | 221 | 0.753 | -15.989 | 17.414 | 38.01% |
| 4 | pepperstone | best_case | 294 | 0.957 | -3.500 | 13.080 | 40.14% |
| 5 | pepperstone | median | 294 | 0.957 | -3.500 | 13.080 | 40.14% |
| 6 | pepperstone | p95 | 294 | 0.904 | -7.744 | 14.578 | 40.14% |
| 7 | dukascopy | best_case | 221 | 0.902 | -6.239 | 12.381 | 38.46% |
| 8 | dukascopy | median | 221 | 0.868 | -8.308 | 13.186 | 38.46% |
| 9 | dukascopy | p95 | 221 | 0.811 | -11.696 | 16.044 | 38.46% |

## Decision

Do not proceed to decile, multisymbol, adversarial, intrabar, or Phase 1 planning for this v0 candidate.

Do not tune `opening_drive_failed_continuation_v0` in place. Any future opening-drive idea must use a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
