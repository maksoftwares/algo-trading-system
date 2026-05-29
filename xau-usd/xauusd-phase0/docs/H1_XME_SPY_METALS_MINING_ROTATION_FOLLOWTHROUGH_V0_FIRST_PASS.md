# H1 XME/SPY Metals Mining Rotation Follow-Through v0 First Pass

Date: 2026-05-30
Status: REJECTED_FIRST_PASS
Expert: `h1_xme_spy_metals_mining_rotation_followthrough_v0`
Hypothesis SHA256: `c54316bc70a6d9baaeddf8502f30103e9ec74da60fee6518258ee4d9e045b87f`

## Decision

Reject v0 without tuning.

The candidate introduced a public XME/SPY metals-mining versus broad equity rotation data class and reached the 40-trade floor in all 9 cells. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Capital.com, Pepperstone, and Dukascopy were all negative after costs.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 104 | 38.46% | 0.8439 | -4.69% | 7.58% | 2 |
| 2 | Capital.com | median | 104 | 38.46% | 0.8439 | -4.69% | 7.58% | 2 |
| 3 | Capital.com | p95 | 104 | 38.46% | 0.8242 | -5.29% | 7.81% | 2 |
| 4 | Pepperstone | best_case | 150 | 41.33% | 0.9615 | -1.51% | 8.46% | 2 |
| 5 | Pepperstone | median | 150 | 41.33% | 0.9615 | -1.51% | 8.46% | 2 |
| 6 | Pepperstone | p95 | 150 | 41.33% | 0.9392 | -2.38% | 8.77% | 2 |
| 7 | Dukascopy | best_case | 133 | 33.83% | 0.7122 | -10.78% | 10.78% | 0 |
| 8 | Dukascopy | median | 133 | 33.83% | 0.6922 | -11.57% | 11.57% | 0 |
| 9 | Dukascopy | p95 | 133 | 33.83% | 0.6617 | -12.64% | 12.64% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,161
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

XME/SPY metals-mining rotation is independent of the retest family, but this fixed follow-through interpretation has no cross-broker cost-adjusted edge. It should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or EA coding under the same v0 hypothesis.
