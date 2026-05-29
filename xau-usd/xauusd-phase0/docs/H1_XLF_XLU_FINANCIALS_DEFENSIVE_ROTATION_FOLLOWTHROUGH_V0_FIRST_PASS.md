# H1 XLF/XLU Financials Defensive Rotation Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_xlf_xlu_financials_defensive_rotation_followthrough_v0`
Hypothesis SHA256: `237448b2966d62527a86e4bca421b8d490dd433ee71cbe67031061f3e4a26bf4`

## Decision

Reject v0 without tuning.

The candidate reached the sample-size floor in all 9 cells, had zero zero-trade months in every cell, and produced positive pockets in Capital.com and Pepperstone. It still failed the first-pass edge gate because 0/9 cells reached PF >= 1.30 and Dukascopy degraded to flat/negative under median/P95 costs.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 176 | 46.02% | 1.1276 | 6.06% | 6.34% | 0 |
| 2 | Capital.com | median | 176 | 46.02% | 1.1276 | 6.06% | 6.34% | 0 |
| 3 | Capital.com | p95 | 176 | 45.45% | 1.1063 | 5.05% | 6.73% | 0 |
| 4 | Pepperstone | best_case | 146 | 43.84% | 1.1307 | 4.85% | 5.73% | 0 |
| 5 | Pepperstone | median | 146 | 43.84% | 1.1307 | 4.85% | 5.73% | 0 |
| 6 | Pepperstone | p95 | 146 | 43.84% | 1.1052 | 3.92% | 5.82% | 0 |
| 7 | Dukascopy | best_case | 174 | 43.68% | 1.0112 | 0.49% | 5.97% | 0 |
| 8 | Dukascopy | median | 174 | 43.68% | 0.9988 | -0.05% | 5.94% | 0 |
| 9 | Dukascopy | p95 | 174 | 41.38% | 0.9298 | -3.03% | 6.93% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,488
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

XLF/XLU sector rotation produced smoother activity than several low-frequency macro candidates, but the edge magnitude was too weak across brokers and cost scenarios. This does not become an approved EA and should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or tuning under the same v0 hypothesis.
