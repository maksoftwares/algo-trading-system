# M15 Inside-Bar Breakout v0 First-Pass Result

Date: 2026-05-23

## Verdict

`m15_inside_bar_breakout_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated enough trades in every matrix cell, but it failed the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30. The best cells were close to breakeven, but the strategy did not show enough cost-adjusted edge to justify decile, multisymbol, adversarial, or Phase 1 planning.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 727 to 854 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 809 | 1.025 | 6.135 | 21.387 | 43.76% |
| 2 | capital_com | median | 809 | 1.025 | 6.135 | 21.387 | 43.76% |
| 3 | capital_com | p95 | 809 | 0.987 | -3.091 | 22.737 | 43.76% |
| 4 | pepperstone | best_case | 854 | 0.969 | -7.362 | 13.505 | 40.16% |
| 5 | pepperstone | median | 854 | 0.969 | -7.362 | 13.505 | 40.16% |
| 6 | pepperstone | p95 | 854 | 0.937 | -14.261 | 16.626 | 40.16% |
| 7 | dukascopy | best_case | 727 | 0.988 | -2.609 | 16.402 | 40.72% |
| 8 | dukascopy | median | 727 | 0.961 | -8.094 | 17.218 | 40.72% |
| 9 | dukascopy | p95 | 727 | 0.908 | -17.954 | 20.401 | 40.72% |

## Decision

Do not proceed to decile, multisymbol, adversarial, intrabar, or Phase 1 planning for this v0 candidate.

Do not tune `m15_inside_bar_breakout_v0` in place. Any future inside-bar or volatility-release idea must use a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
