# A3 ML External Candidate Ranker V1 Result

## Decision

Iteration 5 produced no development survivor. Outcomes after 2020-07 remained closed.

## Predictive evidence

- Fit population, 2018-07 through 2019-06: 153 candidates.
- Development evaluation, 2019-07 through 2020-06: 217 candidates.
- AUC: 0.5155.
- Spearman rank correlation: 0.0298.

Both predictive gates failed: AUC below 0.52 and Spearman below 0.03.

## Economic evidence

| Policy | Trades | Trades/day | Stress PF | Average stress R | Decision |
|---|---:|---:|---:|---:|---|
| Raw all | 151 | 0.576 | 0.632 | -0.2664 | Reject |
| ML top 60% | 138 | 0.527 | 0.614 | -0.2814 | Reject |
| ML top 45% | 122 | 0.466 | 0.619 | -0.2765 | Reject |
| ML top 30% | 22 | 0.084 | 0.754 | -0.1658 | Reject |
| ML top 20% | 9 | 0.034 | 1.132 | 0.0724 | Reject: too small and concentrated |

The nine-trade top-20% slice is not evidence of a tradable model. Removing its top ten winners necessarily leaves a negative result, and its PF remains below the frozen 1.15 gate.

No Python prediction, EA consumption, demo, live, or broker action is authorized.
