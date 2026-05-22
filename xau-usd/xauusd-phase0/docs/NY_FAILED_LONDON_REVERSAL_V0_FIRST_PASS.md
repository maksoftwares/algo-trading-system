# NY Failed London Reversal v0 First-Pass Result

Date: 2026-05-22

## Verdict

`ny_failed_london_reversal_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated sufficient trade count, but it did not satisfy the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 322 to 415 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 322 | 0.918 | -7.332 | 10.572 | 41.30% |
| 2 | capital_com | median | 322 | 0.918 | -7.332 | 10.572 | 41.30% |
| 3 | capital_com | p95 | 322 | 0.872 | -11.361 | 11.418 | 41.30% |
| 4 | pepperstone | best_case | 415 | 1.023 | 2.642 | 12.372 | 41.69% |
| 5 | pepperstone | median | 415 | 1.023 | 2.642 | 12.372 | 41.69% |
| 6 | pepperstone | p95 | 415 | 0.979 | -2.292 | 14.604 | 41.69% |
| 7 | dukascopy | best_case | 386 | 1.037 | 4.038 | 11.496 | 41.71% |
| 8 | dukascopy | median | 386 | 1.007 | 0.701 | 12.603 | 41.71% |
| 9 | dukascopy | p95 | 386 | 0.953 | -4.983 | 14.037 | 41.71% |

## Decision

Do not proceed to decile, multisymbol, adversarial, or Phase 1 planning for this v0 candidate.

Do not tune `ny_failed_london_reversal_v0` in place. Any future London/New York handoff idea must be a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
