# H1 FXF/UUP Safe-Haven FX Rotation Follow-Through v0 First Pass

Date: 2026-05-30
Status: REJECTED_FIRST_PASS
Expert: `h1_fxf_uup_safe_haven_fx_rotation_followthrough_v0`
Hypothesis SHA256: `524f80c39ce72b9115da5094ccd7e6cf56db6c9ad73764d1b45c3b82d634a284`

## Decision

Reject v0 without tuning.

The candidate introduced a public FXF/UUP Swiss-franc-versus-dollar safe-haven FX rotation data class and reached the 40-trade floor in all 9 cells. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Dukascopy was mildly positive below threshold; Capital.com and Pepperstone were negative across cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 147 | 39.46% | 0.8997 | -3.91% | 6.46% | 1 |
| 2 | Capital.com | median | 147 | 39.46% | 0.8997 | -3.91% | 6.46% | 1 |
| 3 | Capital.com | p95 | 147 | 39.46% | 0.8768 | -4.81% | 6.77% | 1 |
| 4 | Pepperstone | best_case | 155 | 40.00% | 0.9346 | -2.78% | 5.38% | 0 |
| 5 | Pepperstone | median | 155 | 40.00% | 0.9346 | -2.78% | 5.38% | 0 |
| 6 | Pepperstone | p95 | 155 | 40.00% | 0.9242 | -3.21% | 5.71% | 0 |
| 7 | Dukascopy | best_case | 168 | 44.05% | 1.0782 | +3.44% | 5.53% | 1 |
| 8 | Dukascopy | median | 168 | 43.45% | 1.0600 | +2.62% | 5.97% | 1 |
| 9 | Dukascopy | p95 | 168 | 42.26% | 1.0052 | +0.23% | 6.82% | 1 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,410
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

FXF/UUP safe-haven FX rotation is independent of the retest family, but this fixed follow-through interpretation has no cross-broker cost-adjusted edge. It should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or EA coding under the same v0 hypothesis.
