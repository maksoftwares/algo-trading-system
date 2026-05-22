# EMR Inactivity Long v0 First-Pass Result

Date: 2026-05-22

## Verdict

`emr_inactivity_long_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis did not satisfy the first Phase 0 research gate. It produced too few trades and did not reach the required profit-factor threshold in any of the 9 matrix cells.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 9 to 10 trades | FAIL |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 9 | 1.293 | 0.586 | 0.991 | 55.56% |
| 2 | capital_com | median | 9 | 1.293 | 0.586 | 0.991 | 55.56% |
| 3 | capital_com | p95 | 9 | 1.197 | 0.401 | 1.011 | 55.56% |
| 4 | pepperstone | best_case | 10 | 0.954 | -0.136 | 1.474 | 40.00% |
| 5 | pepperstone | median | 10 | 0.954 | -0.136 | 1.474 | 40.00% |
| 6 | pepperstone | p95 | 10 | 0.913 | -0.263 | 1.477 | 40.00% |
| 7 | dukascopy | best_case | 9 | 1.097 | 0.240 | 0.986 | 44.44% |
| 8 | dukascopy | median | 9 | 1.020 | 0.050 | 0.993 | 44.44% |
| 9 | dukascopy | p95 | 9 | 0.847 | -0.384 | 1.004 | 44.44% |

## Decision

Do not proceed to decile, multisymbol, adversarial, or Phase 1 planning for this v0 candidate.

Do not tune `emr_inactivity_long_v0` in place. Any future inactivity/exhaustion idea must be a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
