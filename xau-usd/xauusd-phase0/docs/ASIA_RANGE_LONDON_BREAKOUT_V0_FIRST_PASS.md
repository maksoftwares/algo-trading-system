# Asia Range London Breakout v0 First-Pass Result

Date: 2026-05-22

## Verdict

`asia_range_london_breakout_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated sufficient trade count, but it did not satisfy the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30, and several cells also breached drawdown/return tolerance.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 507 to 571 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 537 | 0.743 | -34.547 | 35.825 | 38.18% |
| 2 | capital_com | median | 537 | 0.743 | -34.547 | 35.825 | 38.18% |
| 3 | capital_com | p95 | 537 | 0.696 | -40.108 | 40.899 | 38.18% |
| 4 | pepperstone | best_case | 507 | 0.891 | -16.380 | 26.495 | 38.86% |
| 5 | pepperstone | median | 507 | 0.891 | -16.380 | 26.495 | 38.86% |
| 6 | pepperstone | p95 | 507 | 0.830 | -24.420 | 30.243 | 38.86% |
| 7 | dukascopy | best_case | 571 | 0.783 | -32.386 | 34.543 | 35.55% |
| 8 | dukascopy | median | 571 | 0.747 | -36.634 | 37.907 | 35.55% |
| 9 | dukascopy | p95 | 571 | 0.673 | -44.790 | 45.384 | 35.55% |

## Decision

Do not proceed to decile, multisymbol, adversarial, or Phase 1 planning for this v0 candidate.

Do not tune `asia_range_london_breakout_v0` in place. Any future Asia/London range idea must be a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
