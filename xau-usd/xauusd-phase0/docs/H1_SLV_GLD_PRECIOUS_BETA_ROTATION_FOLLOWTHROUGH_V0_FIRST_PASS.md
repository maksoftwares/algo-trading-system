# H1 SLV/GLD Precious Beta Rotation Follow-Through v0 First Pass

Date: 2026-05-30
Status: REJECTED_FIRST_PASS
Expert: `h1_slv_gld_precious_beta_rotation_followthrough_v0`
Hypothesis SHA256: `df9acb8437447aa717809552c8d4572a6cc4fd19d3aecaacc48ab53f4b54f00f`

## Decision

Reject v0 without tuning.

The candidate introduced a public SLV/GLD precious-beta rotation data class and reached the 40-trade floor in all 9 cells. It failed the first-pass edge gate because only 3/9 cells reached PF >= 1.30. All three passing cells were the Pepperstone window; Capital.com and Dukascopy were negative across cost cases, so the apparent pocket is broker/window-specific and does not qualify as independent diversification.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 159 | 41.51% | 0.9273 | -3.18% | 6.64% | 2 |
| 2 | Capital.com | median | 159 | 41.51% | 0.9273 | -3.18% | 6.64% | 2 |
| 3 | Capital.com | p95 | 159 | 41.51% | 0.9052 | -4.15% | 7.31% | 2 |
| 4 | Pepperstone | best_case | 135 | 48.15% | 1.3813 | 12.73% | 5.54% | 1 |
| 5 | Pepperstone | median | 135 | 48.15% | 1.3813 | 12.73% | 5.54% | 1 |
| 6 | Pepperstone | p95 | 135 | 48.15% | 1.3579 | 11.94% | 5.76% | 1 |
| 7 | Dukascopy | best_case | 163 | 41.72% | 0.9248 | -3.23% | 7.56% | 2 |
| 8 | Dukascopy | median | 163 | 41.72% | 0.8957 | -4.44% | 8.50% | 2 |
| 9 | Dukascopy | p95 | 163 | 41.10% | 0.8516 | -6.27% | 9.85% | 2 |

## Gate Read

```text
PF >= 1.30 cells: 3/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,371
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

SLV/GLD precious-beta rotation is independent of the retest family, but this fixed follow-through interpretation did not produce robust cross-broker cost-adjusted edge. The Pepperstone-only pocket must not be tuned or promoted under v0. Do not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or EA coding for this candidate.
