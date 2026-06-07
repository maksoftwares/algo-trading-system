# H4 Macro Pullback Reclaim v0 First Pass

Generated: 2026-06-07

Expert: `h4_macro_pullback_reclaim_v0`
Hypothesis SHA256: `5db99854d13da8f3c1e12dd6f04717d2082d1bb1f168bd7ce55fb3ef76014b2d`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

Removing D1 trend confirmation preserved some strict-macro edge in Capital.com, but it did not create a worthy EA. The candidate produced 24 to 85 trades per cell, only 4/9 PF cells above 1.30, and failed the trade-count, activity, and cross-broker PF persistence gates.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 24 | 54.17% | 1.6703 | 2.87% | 1.42% | 11.11% | 6 |
| 2 | capital_com | median | 24 | 54.17% | 1.6703 | 2.87% | 1.42% | 11.11% | 6 |
| 3 | capital_com | p95 | 24 | 54.17% | 1.6560 | 2.82% | 1.43% | 11.11% | 6 |
| 4 | pepperstone | best_case | 36 | 41.67% | 1.1476 | 1.05% | 2.77% | 27.78% | 5 |
| 5 | pepperstone | median | 36 | 41.67% | 1.1476 | 1.05% | 2.77% | 27.78% | 5 |
| 6 | pepperstone | p95 | 36 | 41.67% | 1.1412 | 1.01% | 2.79% | 27.78% | 5 |
| 7 | dukascopy | best_case | 85 | 50.59% | 1.3331 | 5.89% | 2.28% | 22.22% | 5 |
| 8 | dukascopy | median | 85 | 50.59% | 1.2481 | 4.38% | 2.52% | 25.00% | 5 |
| 9 | dukascopy | p95 | 85 | 49.41% | 1.2106 | 3.71% | 2.59% | 25.00% | 5 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 4/9 |
| At least 40 trades per cell | FAIL, 3/9 |
| Max zero-trade months <= 3 | FAIL, max 6 |
| Cross-broker persistence | FAIL, Pepperstone below threshold and Dukascopy cost decay |
| Concentration | FAIL, Pepperstone concentration remains extreme |

## Interpretation

This candidate shows that removing D1 confirmation improves activity and keeps Capital.com profitable, but it does not preserve enough of the v0 cross-broker PF clue. The macro family remains meaningful, but not worthy yet.

Do not tune v0. The best macro clue remains `h4_macro_momentum_confluence_v0`, which passed PF in 9/9 cells but was too sparse.

## Evidence

- Hypothesis: `docs/hypothesis_h4_macro_pullback_reclaim_v0.md`
- Registration: `outputs/reports/h4_macro_pullback_reclaim_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_macro_pullback_reclaim_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_macro_pullback_reclaim_v0/`
