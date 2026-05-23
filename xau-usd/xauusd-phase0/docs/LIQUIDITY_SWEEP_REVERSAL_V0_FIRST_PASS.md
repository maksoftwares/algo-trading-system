# Liquidity Sweep Reversal v0 First-Pass Result

Date: 2026-05-23

## Verdict

`liquidity_sweep_reversal_v0` is `REJECTED_FIRST_PASS`.

The locked v0 hypothesis generated sufficient trade count in every matrix cell, but it failed the first Phase 0 research edge gate. None of the 9 matrix cells reached PF >= 1.30, and every cell had negative total return.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 393 to 482 trades | PASS |
| Retune allowed under same name | No | No | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 393 | 0.671 | -33.774 | 34.787 | 35.88% |
| 2 | capital_com | median | 393 | 0.671 | -33.774 | 34.787 | 35.88% |
| 3 | capital_com | p95 | 393 | 0.626 | -38.010 | 38.872 | 35.88% |
| 4 | pepperstone | best_case | 427 | 0.946 | -6.629 | 12.596 | 40.28% |
| 5 | pepperstone | median | 427 | 0.946 | -6.629 | 12.596 | 40.28% |
| 6 | pepperstone | p95 | 427 | 0.900 | -12.093 | 16.516 | 40.28% |
| 7 | dukascopy | best_case | 482 | 0.832 | -20.998 | 25.189 | 38.59% |
| 8 | dukascopy | median | 482 | 0.790 | -25.546 | 27.955 | 38.59% |
| 9 | dukascopy | p95 | 482 | 0.706 | -34.070 | 34.655 | 38.59% |

## Decision

Do not proceed to decile, multisymbol, adversarial, intrabar, or Phase 1 planning for this v0 candidate.

Do not tune `liquidity_sweep_reversal_v0` in place. Any future liquidity-sweep idea must use a new versioned hypothesis with a fresh mechanical definition and hash registration before result-producing runs.
