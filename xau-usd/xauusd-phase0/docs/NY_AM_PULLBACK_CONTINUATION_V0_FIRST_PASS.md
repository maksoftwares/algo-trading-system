# NY AM Pullback Continuation v0 First-Pass Result

Date: 2026-05-22

## Verdict

`ny_am_pullback_continuation_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated sufficient trade count, but it did not satisfy the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 326 to 382 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 382 | 0.943 | -6.081 | 12.002 | 42.41% |
| 2 | capital_com | median | 382 | 0.943 | -6.081 | 12.002 | 42.41% |
| 3 | capital_com | p95 | 382 | 0.898 | -10.896 | 15.651 | 42.41% |
| 4 | pepperstone | best_case | 326 | 0.940 | -5.621 | 12.848 | 39.88% |
| 5 | pepperstone | median | 326 | 0.940 | -5.621 | 12.848 | 39.88% |
| 6 | pepperstone | p95 | 326 | 0.894 | -9.882 | 14.253 | 39.88% |
| 7 | dukascopy | best_case | 357 | 0.966 | -3.526 | 11.575 | 40.06% |
| 8 | dukascopy | median | 357 | 0.944 | -5.675 | 12.347 | 40.06% |
| 9 | dukascopy | p95 | 357 | 0.887 | -11.211 | 15.164 | 40.06% |

## Decision

Do not proceed to decile, multisymbol, adversarial, or Phase 1 planning for this v0 candidate.

Do not tune `ny_am_pullback_continuation_v0` in place. Any future New York opening-drive idea must be a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
