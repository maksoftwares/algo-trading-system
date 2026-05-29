# H1 DBB/UUP Industrial Metals Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_dbb_uup_industrial_metals_followthrough_v0`
Hypothesis: `docs/hypothesis_h1_dbb_uup_industrial_metals_followthrough_v0.md`
Registered SHA256: `9d04a9eff245e4d9d3cf89ca069fa58b17fc3a8ae7f9e34f9a159d53842f4908`

## Decision

Reject v0 without tuning.

The candidate reached the minimum trade-count floor in all 9 cells, but 0/9 cells reached PF >= 1.30. Capital.com was mildly positive but below threshold, Pepperstone was slightly negative, and Dukascopy was negative across cost models. This is a multi-cell expectancy failure, not a sample-size failure.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Max zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 170 | 43.53% | 1.0604 | 2.62% | 1 | 3.69% |
| 2 | capital_com | median | 170 | 43.53% | 1.0604 | 2.62% | 1 | 3.69% |
| 3 | capital_com | p95 | 170 | 43.53% | 1.0232 | 1.00% | 1 | 4.18% |
| 4 | pepperstone | best_case | 140 | 40.71% | 0.9688 | -1.20% | 1 | 8.74% |
| 5 | pepperstone | median | 140 | 40.71% | 0.9688 | -1.20% | 1 | 8.74% |
| 6 | pepperstone | p95 | 140 | 40.71% | 0.9535 | -1.80% | 1 | 9.10% |
| 7 | dukascopy | best_case | 155 | 40.00% | 0.8929 | -4.44% | 2 | 9.35% |
| 8 | dukascopy | median | 155 | 40.00% | 0.8706 | -5.33% | 2 | 9.85% |
| 9 | dukascopy | p95 | 155 | 39.35% | 0.8314 | -6.90% | 2 | 11.16% |

## Gate Snapshot

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total cost-cell trades | 1,395 | Review context | PASS |

## Interpretation

This tested whether shifted public DBB/UUP daily ETF pressure could identify XAU H1 follow-through after industrial metals strengthened against the dollar. The effect did not persist across broker windows or cost models.

Do not tune this v0. A future industrial-metals lane would need a new versioned hypothesis and preferably a stronger input source, such as primary futures/volume or a broader metals-basket signal with a different mechanical thesis.
