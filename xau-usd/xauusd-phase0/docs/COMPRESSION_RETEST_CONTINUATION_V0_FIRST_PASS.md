# Compression Retest Continuation v0 First-Pass Result

Date: 2026-05-22

## Verdict

`compression_retest_continuation_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis did not produce any real-data trades in the 9-cell matrix, so it fails the first Phase 0 research frequency gate before edge can be assessed.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 0 trades in every cell | FAIL |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 0 | 0.000 | 0.000 | 0.000 | 0.00% |
| 2 | capital_com | median | 0 | 0.000 | 0.000 | 0.000 | 0.00% |
| 3 | capital_com | p95 | 0 | 0.000 | 0.000 | 0.000 | 0.00% |
| 4 | pepperstone | best_case | 0 | 0.000 | 0.000 | 0.000 | 0.00% |
| 5 | pepperstone | median | 0 | 0.000 | 0.000 | 0.000 | 0.00% |
| 6 | pepperstone | p95 | 0 | 0.000 | 0.000 | 0.000 | 0.00% |
| 7 | dukascopy | best_case | 0 | 0.000 | 0.000 | 0.000 | 0.00% |
| 8 | dukascopy | median | 0 | 0.000 | 0.000 | 0.000 | 0.00% |
| 9 | dukascopy | p95 | 0 | 0.000 | 0.000 | 0.000 | 0.00% |

## Decision

Do not proceed to decile, multisymbol, adversarial, or Phase 1 planning for this v0 candidate.

Do not tune `compression_retest_continuation_v0` in place. Any future compression/retest idea must be a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
