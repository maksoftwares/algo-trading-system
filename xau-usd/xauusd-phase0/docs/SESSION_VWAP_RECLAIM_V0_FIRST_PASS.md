# Session VWAP Reclaim v0 First-Pass Result

Date: 2026-05-22

## Verdict

`session_vwap_reclaim_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated sufficient trade count, but it did not satisfy the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 481 to 614 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 481 | 0.855 | -19.486 | 30.272 | 39.50% |
| 2 | capital_com | median | 481 | 0.855 | -19.486 | 30.272 | 39.50% |
| 3 | capital_com | p95 | 481 | 0.824 | -23.451 | 32.671 | 39.50% |
| 4 | pepperstone | best_case | 614 | 0.877 | -19.837 | 27.819 | 37.95% |
| 5 | pepperstone | median | 614 | 0.877 | -19.837 | 27.819 | 37.95% |
| 6 | pepperstone | p95 | 614 | 0.845 | -24.494 | 31.020 | 37.95% |
| 7 | dukascopy | best_case | 507 | 0.951 | -7.129 | 16.685 | 39.64% |
| 8 | dukascopy | median | 507 | 0.925 | -10.691 | 18.857 | 39.64% |
| 9 | dukascopy | p95 | 507 | 0.855 | -19.609 | 24.661 | 39.64% |

## Decision

Do not proceed to decile, multisymbol, adversarial, or Phase 1 planning for this v0 candidate.

Do not tune `session_vwap_reclaim_v0` in place. Any future session VWAP/proxy idea must be a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
