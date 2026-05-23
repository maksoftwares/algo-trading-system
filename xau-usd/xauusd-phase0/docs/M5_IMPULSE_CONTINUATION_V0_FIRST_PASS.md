# M5 Impulse Continuation v0 First-Pass Result

Date: 2026-05-23

## Verdict

`m5_impulse_continuation_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated high trade count in every matrix cell, but it failed the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30, and several cells breached the drawdown/total-return catastrophic-failure limits. This is an expectancy rejection, not a sample-size rejection.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 2199 to 2363 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 2199 | 0.879 | -57.736 | 60.386 | 40.52% |
| 2 | capital_com | median | 2199 | 0.879 | -57.736 | 60.386 | 40.52% |
| 3 | capital_com | p95 | 2199 | 0.842 | -68.333 | 70.159 | 40.52% |
| 4 | pepperstone | best_case | 2363 | 0.941 | -33.117 | 37.139 | 39.65% |
| 5 | pepperstone | median | 2363 | 0.941 | -33.117 | 37.139 | 39.65% |
| 6 | pepperstone | p95 | 2363 | 0.897 | -49.512 | 51.612 | 39.65% |
| 7 | dukascopy | best_case | 2220 | 0.993 | -4.375 | 23.761 | 40.81% |
| 8 | dukascopy | median | 2220 | 0.962 | -21.765 | 30.917 | 40.81% |
| 9 | dukascopy | p95 | 2220 | 0.894 | -49.643 | 51.017 | 40.81% |

## Decision

Do not proceed to decile, multisymbol, adversarial, intrabar, or Phase 1 planning for this v0 candidate.

Do not tune `m5_impulse_continuation_v0` in place. Any future impulse-continuation idea must use a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
