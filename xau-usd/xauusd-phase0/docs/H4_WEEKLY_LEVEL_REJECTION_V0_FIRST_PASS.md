# H4 Weekly Level Rejection v0 First Pass

Generated: 2026-06-07

Expert: `h4_weekly_level_rejection_v0`
Hypothesis SHA256: `955606e99b7381dd88a49191c0c5391659507b18e256a39b3a643da353af428e`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

The candidate solved the activity problem and used slower H4 decisions with wider stops, but it did not produce cross-broker edge. Pepperstone passed PF in all cost cells, while Capital.com and Dukascopy were negative across costs. This is a broker-fragmented pocket, not a worthy EA.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 67 | 32.84% | 0.7878 | -4.37% | 8.47% | 58.33% | 2 |
| 2 | capital_com | median | 67 | 32.84% | 0.7878 | -4.37% | 8.47% | 58.33% | 2 |
| 3 | capital_com | p95 | 67 | 32.84% | 0.7843 | -4.44% | 8.53% | 58.33% | 2 |
| 4 | pepperstone | best_case | 55 | 49.09% | 1.4823 | 6.09% | 2.30% | 27.78% | 1 |
| 5 | pepperstone | median | 55 | 49.09% | 1.4823 | 6.09% | 2.30% | 27.78% | 1 |
| 6 | pepperstone | p95 | 55 | 49.09% | 1.4740 | 6.01% | 2.31% | 27.78% | 1 |
| 7 | dukascopy | best_case | 76 | 38.16% | 0.9686 | -0.60% | 5.99% | 44.44% | 1 |
| 8 | dukascopy | median | 76 | 38.16% | 0.9467 | -1.02% | 6.28% | 47.22% | 1 |
| 9 | dukascopy | p95 | 76 | 38.16% | 0.9060 | -1.83% | 6.61% | 47.22% | 1 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 3/9 |
| At least 40 trades per cell | PASS, 9/9 |
| Max zero-trade months <= 3 | PASS, max 2 |
| Cross-broker persistence | FAIL, Pepperstone-only PF pocket |
| Concentration | FAIL context, Capital.com/Dukascopy lose money and show 100% largest/top-5 concentration on net losing ledgers |

## Interpretation

The weekly-level rejection idea was worth testing because it was slower and lower-cost than the M5 retest family. The evidence does not support approval. The behavior may exist in one broker window, but it does not transfer across broker data.

Do not tune v0. If weekly-level behavior is revisited, it needs a materially different mechanism or data class, not a minor threshold adjustment.

## Evidence

- Hypothesis: `docs/hypothesis_h4_weekly_level_rejection_v0.md`
- Registration: `outputs/reports/h4_weekly_level_rejection_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_weekly_level_rejection_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_weekly_level_rejection_v0/`
