# H4 Macro Momentum Confluence v1 First Pass

Generated: 2026-06-07

Expert: `h4_macro_momentum_confluence_v1`
Hypothesis SHA256: `919b70698064d7fefd622834e261d702a6e12533b898509b49a5bd3de648c2a2`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v1 without tuning.

The v1 broadening solved the trade-count problem but destroyed the v0 PF edge. It produced 48 to 89 trades per cell, but 0/9 PF cells reached 1.30. Capital.com and Pepperstone were negative across costs, while Dukascopy was positive but below threshold.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 48 | 45.83% | 0.8932 | -1.18% | 3.80% | 33.33% | 2 |
| 2 | capital_com | median | 48 | 45.83% | 0.8932 | -1.18% | 3.80% | 33.33% | 2 |
| 3 | capital_com | p95 | 48 | 45.83% | 0.8840 | -1.29% | 3.85% | 33.33% | 2 |
| 4 | pepperstone | best_case | 55 | 38.18% | 0.7169 | -3.65% | 4.52% | 41.67% | 4 |
| 5 | pepperstone | median | 55 | 38.18% | 0.7169 | -3.65% | 4.52% | 41.67% | 4 |
| 6 | pepperstone | p95 | 55 | 38.18% | 0.7152 | -3.67% | 4.53% | 41.67% | 4 |
| 7 | dukascopy | best_case | 89 | 41.57% | 1.1193 | 2.34% | 4.43% | 41.67% | 2 |
| 8 | dukascopy | median | 89 | 41.57% | 1.0646 | 1.25% | 4.51% | 41.67% | 2 |
| 9 | dukascopy | p95 | 89 | 41.57% | 1.0491 | 0.94% | 4.62% | 41.67% | 2 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | PASS, 9/9 |
| Max zero-trade months <= 3 | FAIL, max 4 |
| Cross-broker persistence | FAIL, Capital.com and Pepperstone negative |
| Concentration | FAIL context, top-trade concentration remains too high in several cells |

## Interpretation

v1 confirms the shape of the macro-confluence problem: broadening activity by lowering the macro-regime threshold dilutes the independent edge. The v0 clue remains meaningful, but not approval-worthy; v1 is not a useful successor.

Do not tune v1. A future attempt would need a different broadening dimension, not weaker macro votes.

## Evidence

- Hypothesis: `docs/hypothesis_h4_macro_momentum_confluence_v1.md`
- Registration: `outputs/reports/h4_macro_momentum_confluence_v1_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_macro_momentum_confluence_v1_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_macro_momentum_confluence_v1/`
