# London Fix Continuation v0 First-Pass Result

Date: 2026-05-22

## Verdict

`london_fix_continuation_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated sufficient trade count, but it did not satisfy the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30, and the best observed PF was below 1.0.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 463 to 658 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 486 | 0.989 | -1.468 | 9.804 | 41.56% |
| 2 | capital_com | median | 486 | 0.989 | -1.468 | 9.804 | 41.56% |
| 3 | capital_com | p95 | 486 | 0.971 | -3.879 | 10.936 | 41.56% |
| 4 | pepperstone | best_case | 658 | 0.911 | -15.521 | 24.495 | 38.60% |
| 5 | pepperstone | median | 658 | 0.911 | -15.521 | 24.495 | 38.60% |
| 6 | pepperstone | p95 | 658 | 0.894 | -18.180 | 26.404 | 38.60% |
| 7 | dukascopy | best_case | 463 | 0.981 | -2.382 | 10.551 | 39.96% |
| 8 | dukascopy | median | 463 | 0.971 | -3.675 | 11.063 | 39.96% |
| 9 | dukascopy | p95 | 463 | 0.948 | -6.407 | 12.377 | 39.96% |

## Decision

Do not proceed to decile, multisymbol, adversarial, or Phase 1 planning for this v0 candidate.

Do not tune `london_fix_continuation_v0` in place. Any future fix-window idea must be a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
