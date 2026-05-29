# H1 XLU/XLK Defensive Rotation Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_xlu_xlk_defensive_rotation_followthrough_v0`
Hypothesis: `docs/hypothesis_h1_xlu_xlk_defensive_rotation_followthrough_v0.md`
Registered SHA256: `1db81d1a0d41bb21022d35aa1fb5ac6bfeb539a27c090bba46b19c09109f3e73`

## Decision

Reject v0 without tuning.

The candidate reached the minimum trade-count floor in all 9 cells, but 0/9 cells reached PF >= 1.30. Capital.com was mildly positive but below threshold, while Pepperstone and Dukascopy were negative across cost models. This is a cross-venue expectancy failure.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Max zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 172 | 45.35% | 1.0835 | 3.75% | 1 | 8.03% |
| 2 | capital_com | median | 172 | 45.35% | 1.0835 | 3.75% | 1 | 8.03% |
| 3 | capital_com | p95 | 172 | 44.77% | 1.0602 | 2.71% | 1 | 8.47% |
| 4 | pepperstone | best_case | 140 | 38.57% | 0.9293 | -2.67% | 1 | 6.17% |
| 5 | pepperstone | median | 140 | 38.57% | 0.9293 | -2.67% | 1 | 6.17% |
| 6 | pepperstone | p95 | 140 | 38.57% | 0.9121 | -3.33% | 1 | 6.64% |
| 7 | dukascopy | best_case | 180 | 40.56% | 0.9024 | -4.62% | 1 | 12.72% |
| 8 | dukascopy | median | 180 | 40.56% | 0.8771 | -5.78% | 1 | 13.31% |
| 9 | dukascopy | p95 | 180 | 40.00% | 0.8285 | -8.01% | 1 | 14.66% |

## Gate Snapshot

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total cost-cell trades | 1,476 | Review context | PASS |

## Interpretation

This tested whether shifted public XLU/XLK defensive-sector rotation could identify XAU H1 follow-through. The effect did not persist across broker windows, and the negative Pepperstone/Dukascopy blocks reject the thesis for v0.

Do not tune this v0. A future equity-sector rotation lane would need a new versioned hypothesis and a materially different input thesis.
