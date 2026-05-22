# Post Spike Short v0 First-Pass Matrix

Last updated: 2026-05-22

## Verdict

Status: REJECTED_FIRST_PASS

`post_spike_short_v0` failed the first hard matrix gate. It generated enough trades in every cell, but did not reach the required profit-factor threshold in any of the 9 cells.

Decision:

```text
Do not proceed to deciles, multisymbol, adversarial review, or EA planning for this v0 definition.
Do not tune this definition in place.
If revisited later, create a new versioned hypothesis.
```

## Matrix Summary

| Cell | Broker | Cost Model | Trades | PF | Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 194 | 0.8917 | -5.83 | 11.00 | 42.27% |
| 2 | capital_com | median | 194 | 0.8917 | -5.83 | 11.00 | 42.27% |
| 3 | capital_com | p95 | 194 | 0.8392 | -8.68 | 11.75 | 42.27% |
| 4 | pepperstone | best_case | 192 | 1.0181 | 0.99 | 8.04 | 41.67% |
| 5 | pepperstone | median | 192 | 1.0181 | 0.99 | 8.04 | 41.67% |
| 6 | pepperstone | p95 | 192 | 0.9664 | -1.83 | 8.71 | 41.67% |
| 7 | dukascopy | best_case | 234 | 1.0026 | 0.18 | 9.46 | 41.45% |
| 8 | dukascopy | median | 234 | 0.9507 | -3.27 | 10.30 | 41.45% |
| 9 | dukascopy | p95 | 234 | 0.8403 | -10.32 | 13.67 | 41.45% |

## Gate Check

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Trade count | At least 40 trades per active cell | 192-234 trades | PASS |
| Concentration | Largest/top-five winners must not dominate | Several cells fail or are not meaningful because net PnL is weak | FAIL |
| Cost sensitivity | Degradation should not erase edge | P95 cells remain below approval threshold | FAIL |

## Notes

The candidate was worth testing because it targets a different short-side exhaustion behavior from `breakout_retest`. The result is still too weak for Phase 0. The correct action is rejection, not adding extra filters after seeing the matrix.
