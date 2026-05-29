# H1 XLI/XLU Cyclical Defensive Rotation Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_xli_xlu_cyclical_defensive_rotation_followthrough_v0`
Hypothesis SHA256: `d49a2d17a11ffdfbfc4936dd7118343f680c1d9942ac832b77f3a995be3311c2`

## Decision

Reject v0 without tuning.

The candidate reached the sample-size floor in all 9 cells and had zero zero-trade months in every cell. It still failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Capital.com and Pepperstone showed weak positive pockets, but Dukascopy was negative in all cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 161 | 45.96% | 1.1269 | 5.30% | 4.60% | 0 |
| 2 | Capital.com | median | 161 | 45.96% | 1.1269 | 5.30% | 4.60% | 0 |
| 3 | Capital.com | p95 | 161 | 45.34% | 1.0985 | 4.11% | 4.65% | 0 |
| 4 | Pepperstone | best_case | 145 | 45.52% | 1.1851 | 6.93% | 3.73% | 0 |
| 5 | Pepperstone | median | 145 | 45.52% | 1.1851 | 6.93% | 3.73% | 0 |
| 6 | Pepperstone | p95 | 145 | 45.52% | 1.1618 | 6.08% | 3.77% | 0 |
| 7 | Dukascopy | best_case | 169 | 40.24% | 0.9173 | -3.72% | 9.58% | 0 |
| 8 | Dukascopy | median | 169 | 40.24% | 0.8899 | -4.93% | 10.07% | 0 |
| 9 | Dukascopy | p95 | 169 | 39.64% | 0.8410 | -7.10% | 11.38% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,425
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

XLI/XLU sector rotation produced clean sample size and smoother activity than many macro candidates, but the effect is too weak and broker-sensitive. This does not become an approved EA and should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or tuning under the same v0 hypothesis.
