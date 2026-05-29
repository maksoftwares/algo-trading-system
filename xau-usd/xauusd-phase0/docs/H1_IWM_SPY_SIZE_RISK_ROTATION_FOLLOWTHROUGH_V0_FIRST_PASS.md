# H1 IWM/SPY Size Risk Rotation Follow-Through v0 First Pass

Date: 2026-05-30
Status: REJECTED_FIRST_PASS
Expert: `h1_iwm_spy_size_risk_rotation_followthrough_v0`
Hypothesis SHA256: `07348d464f6e70cedd05365610af81096a9dc7a2d511353363facd78dd4deba8`

## Decision

Reject v0 without tuning.

The candidate introduced an IWM/SPY size-risk rotation data class and reached the 40-trade floor in all 9 cells. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Pepperstone was slightly positive but below threshold, while Capital.com was negative and Dukascopy weakened under higher costs.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 100 | 38.00% | 0.7358 | -7.48% | 11.60% | 0 |
| 2 | Capital.com | median | 100 | 38.00% | 0.7358 | -7.48% | 11.60% | 0 |
| 3 | Capital.com | p95 | 100 | 37.00% | 0.7200 | -7.95% | 11.97% | 0 |
| 4 | Pepperstone | best_case | 124 | 41.94% | 1.0295 | 0.95% | 5.42% | 0 |
| 5 | Pepperstone | median | 124 | 41.94% | 1.0295 | 0.95% | 5.42% | 0 |
| 6 | Pepperstone | p95 | 124 | 41.94% | 1.0103 | 0.33% | 5.61% | 0 |
| 7 | Dukascopy | best_case | 154 | 42.21% | 0.9816 | -0.73% | 6.05% | 0 |
| 8 | Dukascopy | median | 154 | 42.21% | 0.9534 | -1.85% | 6.37% | 0 |
| 9 | Dukascopy | p95 | 154 | 41.56% | 0.9061 | -3.69% | 7.33% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,134
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

IWM/SPY size-risk rotation is independent of the retest family, but this fixed follow-through interpretation has no cost-adjusted edge across the broker matrix. It should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or tuning under the same v0 hypothesis.
