# H4 Macro Momentum Confluence v0 First Pass

Generated: 2026-06-07

Expert: `h4_macro_momentum_confluence_v0`
Hypothesis SHA256: `6465c4537a998573a26800c3d49cbf8575c5a4141b63fc49bc312839dd2d2ebf`
Status: `REJECTED_FIRST_PASS_SPARSE_PF_LEAD`

## Verdict

Reject v0 without tuning.

This is a meaningful independent macro clue, but not a worthy EA. The candidate reached PF above 1.30 in 9/9 broker/cost cells and all cells were profitable, but the sample was far too sparse at 5 to 30 trades per cell. Activity, trade-count, and concentration gates failed.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 12 | 58.33% | 2.2455 | 2.25% | 0.50% | 8.33% | 7 |
| 2 | capital_com | median | 12 | 58.33% | 2.2455 | 2.25% | 0.50% | 8.33% | 7 |
| 3 | capital_com | p95 | 12 | 58.33% | 2.2263 | 2.22% | 0.50% | 8.33% | 7 |
| 4 | pepperstone | best_case | 5 | 80.00% | 4.1515 | 1.30% | 0.40% | 2.78% | 17 |
| 5 | pepperstone | median | 5 | 80.00% | 4.1515 | 1.30% | 0.40% | 2.78% | 17 |
| 6 | pepperstone | p95 | 5 | 80.00% | 4.1288 | 1.29% | 0.41% | 2.78% | 17 |
| 7 | dukascopy | best_case | 30 | 53.33% | 1.4255 | 2.18% | 1.63% | 13.89% | 10 |
| 8 | dukascopy | median | 30 | 53.33% | 1.3409 | 1.76% | 1.67% | 13.89% | 10 |
| 9 | dukascopy | p95 | 30 | 53.33% | 1.3097 | 1.60% | 1.69% | 13.89% | 10 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | PASS, 9/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Max zero-trade months <= 3 | FAIL, max 17 |
| Cross-broker persistence | PASS clue, all brokers/costs profitable and above PF threshold |
| Concentration | FAIL, sample is too sparse and top-5 trade contribution is extreme |

## Interpretation

This is the strongest independent macro clue found after the cost-suspended retest family. It combines shifted macro state, shifted D1 trend, and H4 pullback/reclaim execution. The clue is cross-broker and P95-cost persistent, but the event definition is too restrictive to approve.

Do not tune v0. A new version may broaden the macro-regime evidence mechanically under a fresh SHA, but v0 itself is rejected.

## Evidence

- Hypothesis: `docs/hypothesis_h4_macro_momentum_confluence_v0.md`
- Registration: `outputs/reports/h4_macro_momentum_confluence_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_macro_momentum_confluence_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_macro_momentum_confluence_v0/`
