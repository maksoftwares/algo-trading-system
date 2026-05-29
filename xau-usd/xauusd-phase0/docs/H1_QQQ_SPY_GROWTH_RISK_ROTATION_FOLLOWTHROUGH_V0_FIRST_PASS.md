# H1 QQQ/SPY Growth Risk Rotation Follow-Through v0 First Pass

Date: 2026-05-30
Status: REJECTED_FIRST_PASS
Expert: `h1_qqq_spy_growth_risk_rotation_followthrough_v0`
Hypothesis SHA256: `b8475126b6903bd8a08cf0d6879b12599cac9faa0e13c0119545b829b120a676`

## Decision

Reject v0 without tuning.

The candidate introduced a QQQ/SPY growth-risk rotation data class and reached the 40-trade floor in all 9 cells. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Pepperstone was mildly positive but below threshold, while Capital.com and Dukascopy were negative.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 80 | 40.00% | 0.9208 | -1.74% | 6.07% | 0 |
| 2 | Capital.com | median | 80 | 40.00% | 0.9208 | -1.74% | 6.07% | 0 |
| 3 | Capital.com | p95 | 80 | 40.00% | 0.9063 | -2.06% | 6.25% | 0 |
| 4 | Pepperstone | best_case | 113 | 42.48% | 1.0611 | 1.87% | 5.19% | 0 |
| 5 | Pepperstone | median | 113 | 42.48% | 1.0611 | 1.87% | 5.19% | 0 |
| 6 | Pepperstone | p95 | 113 | 42.48% | 1.0457 | 1.41% | 5.24% | 0 |
| 7 | Dukascopy | best_case | 146 | 33.56% | 0.6606 | -13.54% | 15.51% | 0 |
| 8 | Dukascopy | median | 146 | 33.56% | 0.6365 | -14.58% | 16.43% | 0 |
| 9 | Dukascopy | p95 | 146 | 32.88% | 0.5982 | -16.00% | 17.63% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,017
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

QQQ/SPY growth-risk rotation is genuinely independent of the retest family, but this fixed follow-through interpretation has no cost-adjusted edge across the broker matrix. It should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or tuning under the same v0 hypothesis.
