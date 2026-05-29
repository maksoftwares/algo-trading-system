# H1 XLE/XLU Energy Defensive Rotation Follow-Through v0 First Pass

Date: 2026-05-30
Status: REJECTED_FIRST_PASS
Expert: `h1_xle_xlu_energy_defensive_rotation_followthrough_v0`
Hypothesis SHA256: `626a2afc654ef7661170d78a75af5bd321ad0349d3422a3bd78c476552dfb237`

## Decision

Reject v0 without tuning.

The candidate introduced a public XLE/XLU energy-defensive sector rotation data class and reached the 40-trade floor in all 9 cells. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Pepperstone was mildly positive but below threshold, while Capital.com and Dukascopy were negative across cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 135 | 37.78% | 0.8098 | -7.32% | 8.57% | 1 |
| 2 | Capital.com | median | 135 | 37.78% | 0.8098 | -7.32% | 8.57% | 1 |
| 3 | Capital.com | p95 | 135 | 37.78% | 0.7887 | -8.14% | 9.25% | 1 |
| 4 | Pepperstone | best_case | 117 | 43.59% | 1.0946 | 2.82% | 3.88% | 1 |
| 5 | Pepperstone | median | 117 | 43.59% | 1.0946 | 2.82% | 3.88% | 1 |
| 6 | Pepperstone | p95 | 117 | 43.59% | 1.0691 | 2.07% | 3.97% | 1 |
| 7 | Dukascopy | best_case | 142 | 40.14% | 0.9438 | -2.11% | 5.09% | 1 |
| 8 | Dukascopy | median | 142 | 40.14% | 0.9226 | -2.88% | 5.04% | 1 |
| 9 | Dukascopy | p95 | 142 | 40.14% | 0.8665 | -4.97% | 6.44% | 1 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,182
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

XLE/XLU energy-defensive rotation is independent of the retest family, but this fixed follow-through interpretation has no cross-broker cost-adjusted edge. The sub-threshold Pepperstone pocket must not be tuned or promoted under v0. Do not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or EA coding for this candidate.
