# H1 FXY/UUP Safe-Haven FX Rotation Follow-Through v0 First Pass

Date: 2026-05-30
Status: REJECTED_FIRST_PASS
Expert: `h1_fxy_uup_safe_haven_fx_rotation_followthrough_v0`
Hypothesis SHA256: `5371fc5021873c35f2e0867ae91be257abed4fb6db039356e8b3bc56ab67a576`

## Decision

Reject v0 without tuning.

The candidate introduced a public FXY/UUP yen-versus-dollar safe-haven FX rotation data class and reached the 40-trade floor in all 9 cells. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Pepperstone was mildly positive below threshold; Capital.com and Dukascopy were negative across cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 174 | 40.23% | 0.9190 | -3.73% | 7.50% | 1 |
| 2 | Capital.com | median | 174 | 40.23% | 0.9190 | -3.73% | 7.50% | 1 |
| 3 | Capital.com | p95 | 174 | 40.23% | 0.8921 | -4.97% | 8.30% | 1 |
| 4 | Pepperstone | best_case | 140 | 42.14% | 1.0285 | +1.12% | 6.05% | 1 |
| 5 | Pepperstone | median | 140 | 42.14% | 1.0285 | +1.12% | 6.05% | 1 |
| 6 | Pepperstone | p95 | 140 | 42.14% | 1.0100 | +0.39% | 6.23% | 1 |
| 7 | Dukascopy | best_case | 178 | 39.89% | 0.9383 | -2.98% | 9.32% | 0 |
| 8 | Dukascopy | median | 178 | 39.89% | 0.9230 | -3.68% | 9.65% | 0 |
| 9 | Dukascopy | p95 | 178 | 39.33% | 0.8767 | -5.84% | 10.66% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,476
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

FXY/UUP safe-haven FX rotation is independent of the retest family, but this fixed follow-through interpretation has no cross-broker cost-adjusted edge. It should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or EA coding under the same v0 hypothesis.
