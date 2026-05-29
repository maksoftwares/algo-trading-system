# H1 EURJPY/USDJPY FX Risk Rotation Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_eurjpy_usdjpy_fx_risk_rotation_followthrough_v0`
Hypothesis SHA256: `83749e46378fd9bcc255a8889176660b52d49c3f3a73960cf71238391f534b8e`

## Decision

Reject v0 without tuning.

The candidate reached the sample-size floor in all 9 cells and had zero zero-trade months in every cell. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Capital.com was negative, Pepperstone was positive but below threshold, and Dukascopy was strongly negative.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 108 | 39.81% | 0.8822 | -3.58% | 8.27% | 0 |
| 2 | Capital.com | median | 108 | 39.81% | 0.8822 | -3.58% | 8.27% | 0 |
| 3 | Capital.com | p95 | 108 | 39.81% | 0.8567 | -4.36% | 8.63% | 0 |
| 4 | Pepperstone | best_case | 90 | 44.44% | 1.1217 | 2.63% | 5.72% | 0 |
| 5 | Pepperstone | median | 90 | 44.44% | 1.1217 | 2.63% | 5.72% | 0 |
| 6 | Pepperstone | p95 | 90 | 44.44% | 1.1094 | 2.36% | 5.82% | 0 |
| 7 | Dukascopy | best_case | 121 | 31.40% | 0.5753 | -15.01% | 15.65% | 0 |
| 8 | Dukascopy | median | 121 | 31.40% | 0.5598 | -15.52% | 16.10% | 0 |
| 9 | Dukascopy | p95 | 121 | 31.40% | 0.5266 | -16.63% | 17.14% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 957
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

EURJPY/USDJPY risk rotation is a genuinely independent FX-cross data class, but this fixed follow-through interpretation does not survive the matrix. This does not become an approved EA and should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or tuning under the same v0 hypothesis.
