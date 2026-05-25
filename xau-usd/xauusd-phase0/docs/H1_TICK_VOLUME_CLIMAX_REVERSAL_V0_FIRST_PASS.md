# H1 Tick Volume Climax Reversal v0 First Pass

Status: `REJECTED_FIRST_PASS`

`h1_tick_volume_climax_reversal_v0` was registered, hash-locked, smoke-tested, and run through the real 9-cell research matrix without tuning. It is rejected because it failed the multi-cell PF survival gate and also failed sample-size/activity in the Dukascopy window.

## Gate Summary

| Gate | Requirement | Observed | Status |
| --- | --- | --- | --- |
| PF cell survival | At least 7 of 9 cells with PF >= 1.30 | 0 of 9 | FAIL |
| Minimum trade count | At least 40 trades per matrix cell | 0 to 495 trades | FAIL |
| Catastrophic loss | Max drawdown <= 30% and total return >= -25% in every cell | Max DD 34.90%, worst return -34.20% | FAIL |
| Concentration | Largest/top-5 trade contribution within caps | Concentration gate failed in all cells | FAIL |
| Activity | Max zero-trade months <= 3 | Dukascopy had 36 zero-trade months | FAIL |
| Cost sensitivity | P95 PF / best-case PF >= threshold | Failed in Dukascopy pair because no trades fired | FAIL |

## Matrix Cells

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 495 | 0.746 | -31.308 | 32.849 | 35.76% |
| 2 | capital_com | median | 495 | 0.746 | -31.308 | 32.849 | 35.76% |
| 3 | capital_com | p95 | 495 | 0.720 | -34.199 | 34.902 | 35.76% |
| 4 | pepperstone | best_case | 473 | 1.066 | 8.223 | 12.495 | 42.71% |
| 5 | pepperstone | median | 473 | 1.066 | 8.223 | 12.495 | 42.71% |
| 6 | pepperstone | p95 | 473 | 1.040 | 4.974 | 13.801 | 42.71% |
| 7 | dukascopy | best_case | 0 | 0.000 | 0.000 | 0.000 | 0.00% |
| 8 | dukascopy | median | 0 | 0.000 | 0.000 | 0.000 | 0.00% |
| 9 | dukascopy | p95 | 0 | 0.000 | 0.000 | 0.000 | 0.00% |

## Decision

Do not proceed to deciles, multisymbol, intrabar, or Gate 9 for this version.

Do not tune `h1_tick_volume_climax_reversal_v0` in place. Any future participation-based revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

## Research Impact

This failure is useful because it shows tick-volume climax is not broker-stable in the current normalized data. The active Phase 1 soak and Phase 2 readiness remain unchanged.
