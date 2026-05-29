# H1 TLT/SHY Duration Rotation Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_tlt_shy_duration_rotation_followthrough_v0`
Hypothesis: `docs/hypothesis_h1_tlt_shy_duration_rotation_followthrough_v0.md`
Registered SHA256: `2ccce274004fac24de6ea1e514a9c861d884d20b5cf4d419ba5e66874c9c6c12`

## Decision

Reject v0 without tuning.

The candidate reached the minimum trade-count floor in all 9 cells, but 0/9 cells reached PF >= 1.30. Pepperstone and Dukascopy had mild positive pockets below threshold, while Capital.com was negative. This is a cross-venue expectancy failure.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Max zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 176 | 41.48% | 0.9282 | -3.54% | 1 | 12.14% |
| 2 | capital_com | median | 176 | 41.48% | 0.9282 | -3.54% | 1 | 12.14% |
| 3 | capital_com | p95 | 176 | 40.91% | 0.9063 | -4.62% | 1 | 12.46% |
| 4 | pepperstone | best_case | 140 | 43.57% | 1.0916 | 3.29% | 2 | 5.67% |
| 5 | pepperstone | median | 140 | 43.57% | 1.0916 | 3.29% | 2 | 5.67% |
| 6 | pepperstone | p95 | 140 | 43.57% | 1.0583 | 2.10% | 2 | 5.84% |
| 7 | dukascopy | best_case | 173 | 44.51% | 1.0253 | 1.18% | 1 | 8.72% |
| 8 | dukascopy | median | 173 | 44.51% | 1.0169 | 0.77% | 1 | 8.82% |
| 9 | dukascopy | p95 | 173 | 42.77% | 0.9629 | -1.70% | 1 | 10.45% |

## Gate Snapshot

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total cost-cell trades | 1,467 | Review context | PASS |

## Interpretation

This tested whether shifted public TLT/SHY duration pressure could identify XAU H1 follow-through. The effect did not persist strongly enough across broker windows, and all cells remained below the first-pass PF threshold.

Do not tune this v0. A future duration lane would need a new versioned hypothesis and a materially different rate-data input, such as primary futures, yields, or swap data.
