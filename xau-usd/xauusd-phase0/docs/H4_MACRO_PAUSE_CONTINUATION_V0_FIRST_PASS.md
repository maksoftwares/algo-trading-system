# H4 Macro Pause Continuation v0 First Pass

Generated: 2026-06-07

Expert: `h4_macro_pause_continuation_v0`
Hypothesis SHA256: `b418aa714b6913f3c1421414b77c940faa50088aed331d4cd8bf416e0fc7b1a9`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

The candidate kept the strict macro-composite regime and removed the D1 trend gate, but the H4 pause-continuation execution lost the sparse PF edge. It produced 28 to 69 trades per cell, only 3/9 cells met the 40-trade floor, and 0/9 cells reached PF above 1.30.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 32 | 34.38% | 0.4082 | -5.46% | 5.59% | 44.44% | 5 |
| 2 | capital_com | median | 32 | 34.38% | 0.4082 | -5.46% | 5.59% | 44.44% | 5 |
| 3 | capital_com | p95 | 32 | 34.38% | 0.4102 | -5.38% | 5.56% | 44.44% | 5 |
| 4 | pepperstone | best_case | 28 | 39.29% | 0.9699 | -0.17% | 5.19% | 25.00% | 5 |
| 5 | pepperstone | median | 28 | 39.29% | 0.9699 | -0.17% | 5.19% | 25.00% | 5 |
| 6 | pepperstone | p95 | 28 | 39.29% | 0.9732 | -0.15% | 5.19% | 25.00% | 5 |
| 7 | dukascopy | best_case | 69 | 43.48% | 1.0212 | 0.31% | 4.93% | 36.11% | 4 |
| 8 | dukascopy | median | 69 | 43.48% | 1.0040 | 0.06% | 5.06% | 36.11% | 4 |
| 9 | dukascopy | p95 | 69 | 42.03% | 0.9294 | -1.03% | 5.78% | 36.11% | 4 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | FAIL, 3/9 |
| Max zero-trade months <= 3 | FAIL, max 5 |
| Cross-broker persistence | FAIL, no broker reached PF threshold |
| Concentration | FAIL, top-trade concentration remains extreme |

## Interpretation

This falsifies the pause-continuation broadening path. Removing D1 confirmation increased activity over `h4_macro_momentum_confluence_v0` in some cells, but it also removed the quality needed for cross-broker profitability. The best independent macro clue remains `h4_macro_momentum_confluence_v0`, which passed PF in 9/9 cells but was too sparse.

Do not tune v0. A future independent attempt should use a different data class or a materially different macro execution concept, not another threshold relaxation of this pause-continuation lane.

## Evidence

- Hypothesis: `docs/hypothesis_h4_macro_pause_continuation_v0.md`
- Registration: `outputs/reports/h4_macro_pause_continuation_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_macro_pause_continuation_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_macro_pause_continuation_v0/`
