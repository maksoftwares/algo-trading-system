# Asia Range London Failed Break Reversal v0 First-Pass Result

Date: 2026-05-22

## Verdict

`asia_range_london_failed_break_reversal_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated sufficient trade count, but it did not satisfy the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 326 to 372 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 336 | 0.714 | -25.035 | 28.188 | 37.80% |
| 2 | capital_com | median | 336 | 0.714 | -25.035 | 28.188 | 37.80% |
| 3 | capital_com | p95 | 336 | 0.664 | -29.203 | 31.844 | 37.80% |
| 4 | pepperstone | best_case | 326 | 0.958 | -4.058 | 14.938 | 40.80% |
| 5 | pepperstone | median | 326 | 0.958 | -4.058 | 14.938 | 40.80% |
| 6 | pepperstone | p95 | 326 | 0.893 | -10.182 | 17.529 | 40.80% |
| 7 | dukascopy | best_case | 372 | 0.832 | -17.300 | 21.570 | 37.10% |
| 8 | dukascopy | median | 372 | 0.792 | -20.879 | 24.663 | 37.10% |
| 9 | dukascopy | p95 | 372 | 0.706 | -28.380 | 31.093 | 37.10% |

## Decision

Do not proceed to decile, multisymbol, adversarial, or Phase 1 planning for this v0 candidate.

Do not tune `asia_range_london_failed_break_reversal_v0` in place. Any future Asia/London failed-auction idea must be a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
