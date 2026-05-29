# H1 AUDJPY/USDJPY FX Carry Rotation Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_audjpy_usdjpy_fx_carry_rotation_followthrough_v0`
Hypothesis SHA256: `ae09a355182802383b4b76f3fee5bdaffcfeae4a14eb74ed0fbaf0e37e78084f`

## Decision

Reject v0 without tuning.

The candidate reached the sample-size floor in all 9 cells and had zero zero-trade months in every cell. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Capital.com was negative, Pepperstone was only mildly positive below threshold, and Dukascopy was strongly negative.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 109 | 40.37% | 0.8878 | -3.45% | 7.33% | 0 |
| 2 | Capital.com | median | 109 | 40.37% | 0.8878 | -3.45% | 7.33% | 0 |
| 3 | Capital.com | p95 | 109 | 40.37% | 0.8729 | -3.92% | 7.54% | 0 |
| 4 | Pepperstone | best_case | 128 | 44.53% | 1.0636 | 2.01% | 5.61% | 0 |
| 5 | Pepperstone | median | 128 | 44.53% | 1.0636 | 2.01% | 5.61% | 0 |
| 6 | Pepperstone | p95 | 128 | 44.53% | 1.0469 | 1.48% | 5.87% | 0 |
| 7 | Dukascopy | best_case | 144 | 35.42% | 0.6816 | -13.11% | 13.73% | 0 |
| 8 | Dukascopy | median | 144 | 35.42% | 0.6608 | -13.88% | 14.45% | 0 |
| 9 | Dukascopy | p95 | 144 | 35.42% | 0.6247 | -15.26% | 15.80% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,143
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

AUDJPY/USDJPY carry-risk rotation is a genuinely independent FX-cross data class, but this fixed follow-through interpretation does not survive the matrix. This does not become an approved EA and should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or tuning under the same v0 hypothesis.
