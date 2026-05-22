# Squeeze Breakout Long v0 First-Pass Matrix

Last updated: 2026-05-22

## Verdict

Status: REJECTED_FIRST_PASS

`squeeze_breakout_long_v0` failed the first hard matrix gate. It produced enough trades, but did not reach the required profit-factor threshold in any of the 9 cells.

Decision:

```text
Do not proceed to deciles, multisymbol, adversarial review, or EA planning for this v0 definition.
Do not tune this definition in place.
If revisited later, create a new versioned hypothesis.
```

## Matrix Summary

| Cell | Broker | Cost Model | Trades | PF | Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 195 | 0.8811 | -6.46 | 8.94 | 38.97% |
| 2 | capital_com | median | 195 | 0.8811 | -6.46 | 8.94 | 38.97% |
| 3 | capital_com | p95 | 195 | 0.8606 | -7.61 | 9.96 | 38.97% |
| 4 | pepperstone | best_case | 211 | 1.1420 | 8.46 | 5.07 | 44.08% |
| 5 | pepperstone | median | 211 | 1.1420 | 8.46 | 5.07 | 44.08% |
| 6 | pepperstone | p95 | 211 | 1.1234 | 7.36 | 5.31 | 44.08% |
| 7 | dukascopy | best_case | 194 | 1.1169 | 6.31 | 4.54 | 43.30% |
| 8 | dukascopy | median | 194 | 1.0933 | 5.00 | 4.76 | 43.30% |
| 9 | dukascopy | p95 | 194 | 1.0411 | 2.19 | 5.83 | 43.30% |

## Gate Check

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF | PF >= 1.30 in at least 7 of 9 cells | 0 of 9 cells | FAIL |
| Trade count | At least 40 trades per active cell | 194-211 trades | PASS |
| Cost sensitivity | Degradation should not erase edge | P95 PF remains below approval threshold | FAIL |

## Notes

The candidate does show positive returns in the Pepperstone and Dukascopy cells, but the edge is too weak versus the Phase 0 acceptance standard. The correct action is rejection, not filter addition.
