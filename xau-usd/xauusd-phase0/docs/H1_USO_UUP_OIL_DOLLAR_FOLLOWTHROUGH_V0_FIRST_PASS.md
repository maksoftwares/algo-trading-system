# H1 USO/UUP Oil-Dollar Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_uso_uup_oil_dollar_followthrough_v0`
Hypothesis: `docs/hypothesis_h1_uso_uup_oil_dollar_followthrough_v0.md`
Registered SHA256: `093247902a7065489e03ab885257a432cdae916426df57022b50e1d302cac254`

## Decision

Reject v0 without tuning.

The candidate reached the minimum trade-count floor in all 9 cells, but 0/9 cells reached PF >= 1.30. Pepperstone was mildly positive below threshold, while Capital.com was slightly negative and Dukascopy was materially negative. This is a cross-venue expectancy failure.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Max zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 154 | 42.86% | 0.9865 | -0.57% | 2 | 7.90% |
| 2 | capital_com | median | 154 | 42.86% | 0.9865 | -0.57% | 2 | 7.90% |
| 3 | capital_com | p95 | 154 | 42.86% | 0.9526 | -2.01% | 2 | 8.31% |
| 4 | pepperstone | best_case | 144 | 43.75% | 1.0875 | 3.27% | 2 | 5.52% |
| 5 | pepperstone | median | 144 | 43.75% | 1.0875 | 3.27% | 2 | 5.52% |
| 6 | pepperstone | p95 | 144 | 43.75% | 1.0678 | 2.53% | 2 | 5.75% |
| 7 | dukascopy | best_case | 153 | 35.29% | 0.7790 | -9.34% | 1 | 12.54% |
| 8 | dukascopy | median | 153 | 35.29% | 0.7596 | -10.11% | 1 | 12.77% |
| 9 | dukascopy | p95 | 153 | 35.29% | 0.7183 | -11.79% | 1 | 13.90% |

## Gate Snapshot

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total cost-cell trades | 1,353 | Review context | PASS |

## Interpretation

This tested whether shifted public USO/UUP crude-oil-versus-dollar pressure could identify XAU H1 follow-through. The effect did not persist across broker windows, and the negative Capital.com/Dukascopy blocks reject the thesis for v0.

Do not tune this v0. A future oil-dollar lane would need a new versioned hypothesis and a materially different input thesis or a better primary crude-oil data source.
