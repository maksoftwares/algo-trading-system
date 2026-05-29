# H1 EEM/SPY EM Risk Rotation Follow-Through v0 First Pass

Date: 2026-05-30
Status: REJECTED_FIRST_PASS
Expert: `h1_eem_spy_em_risk_rotation_followthrough_v0`
Hypothesis SHA256: `8e10df3f697fd8038970cd0bf06076e869656b2107548e7b4189e546ae963b4d`

## Decision

Reject v0 without tuning.

The candidate introduced a public EEM/SPY emerging-market risk rotation data class and reached the 40-trade floor in all 9 cells. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Capital.com and Pepperstone were near flat or mildly negative after costs; Dukascopy was materially negative across cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 102 | 42.16% | 0.9829 | -0.47% | 4.40% | 2 |
| 2 | Capital.com | median | 102 | 42.16% | 0.9829 | -0.47% | 4.40% | 2 |
| 3 | Capital.com | p95 | 102 | 42.16% | 0.9610 | -1.09% | 4.49% | 2 |
| 4 | Pepperstone | best_case | 155 | 41.29% | 1.0064 | 0.26% | 4.49% | 1 |
| 5 | Pepperstone | median | 155 | 41.29% | 1.0064 | 0.26% | 4.49% | 1 |
| 6 | Pepperstone | p95 | 155 | 41.29% | 0.9852 | -0.59% | 5.16% | 1 |
| 7 | Dukascopy | best_case | 139 | 35.25% | 0.6643 | -12.96% | 13.14% | 1 |
| 8 | Dukascopy | median | 139 | 35.25% | 0.6514 | -13.47% | 13.66% | 1 |
| 9 | Dukascopy | p95 | 139 | 34.53% | 0.6082 | -15.02% | 15.09% | 1 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,188
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

EEM/SPY EM-risk rotation is independent of the retest family, but this fixed follow-through interpretation has no cross-broker cost-adjusted edge. It should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or EA coding under the same v0 hypothesis.
