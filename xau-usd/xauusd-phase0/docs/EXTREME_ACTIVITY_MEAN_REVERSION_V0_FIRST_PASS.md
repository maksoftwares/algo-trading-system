# Extreme Activity Mean Reversion v0 First-Pass Result

Date: 2026-05-22

## Verdict

`extreme_activity_mean_reversion_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated sufficient trade count, but it did not satisfy the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 74 to 176 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 74 | 0.753 | -5.483 | 7.767 | 35.14% |
| 2 | capital_com | median | 74 | 0.753 | -5.483 | 7.767 | 35.14% |
| 3 | capital_com | p95 | 74 | 0.730 | -6.053 | 8.198 | 35.14% |
| 4 | pepperstone | best_case | 102 | 0.879 | -3.664 | 9.408 | 37.25% |
| 5 | pepperstone | median | 102 | 0.879 | -3.664 | 9.408 | 37.25% |
| 6 | pepperstone | p95 | 102 | 0.853 | -4.486 | 9.666 | 37.25% |
| 7 | dukascopy | best_case | 176 | 0.882 | -5.870 | 9.183 | 38.07% |
| 8 | dukascopy | median | 176 | 0.854 | -7.148 | 10.177 | 38.07% |
| 9 | dukascopy | p95 | 176 | 0.799 | -9.777 | 12.486 | 38.07% |

## Decision

Do not proceed to decile, multisymbol, adversarial, or Phase 1 planning for this v0 candidate.

Do not tune `extreme_activity_mean_reversion_v0` in place. Any future high-activity fade idea must be a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
