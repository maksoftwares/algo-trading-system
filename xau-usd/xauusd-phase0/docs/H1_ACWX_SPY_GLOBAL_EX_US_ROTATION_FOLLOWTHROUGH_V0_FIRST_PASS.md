# H1 ACWX/SPY Global Ex-US Rotation Follow-Through v0 First Pass

Date: 2026-05-30
Status: REJECTED_FIRST_PASS
Expert: `h1_acwx_spy_global_ex_us_rotation_followthrough_v0`
Hypothesis SHA256: `70ddcea7e2e47eaaf06165c2cc69b4fba09186b9f21cafde7ef2846612d2a892`

## Decision

Reject v0 without tuning.

The candidate introduced a public ACWX/SPY global ex-US versus US equity rotation data class and reached the 40-trade floor in all 9 cells. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30. Capital.com and Dukascopy were negative across cost cases; Pepperstone was positive but stayed below threshold.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 89 | 37.08% | 0.7261 | -7.23% | 9.14% | 2 |
| 2 | Capital.com | median | 89 | 37.08% | 0.7261 | -7.23% | 9.14% | 2 |
| 3 | Capital.com | p95 | 89 | 35.96% | 0.7119 | -7.63% | 9.47% | 2 |
| 4 | Pepperstone | best_case | 117 | 42.74% | 1.0638 | +1.96% | 4.39% | 3 |
| 5 | Pepperstone | median | 117 | 42.74% | 1.0638 | +1.96% | 4.39% | 3 |
| 6 | Pepperstone | p95 | 117 | 42.74% | 1.0458 | +1.41% | 4.54% | 3 |
| 7 | Dukascopy | best_case | 130 | 36.15% | 0.7074 | -10.35% | 10.35% | 1 |
| 8 | Dukascopy | median | 130 | 35.38% | 0.6980 | -10.67% | 10.67% | 1 |
| 9 | Dukascopy | p95 | 130 | 35.38% | 0.6594 | -12.06% | 12.06% | 1 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 1,008
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

ACWX/SPY global ex-US rotation is independent of the retest family, but this fixed follow-through interpretation has no cross-broker cost-adjusted edge. It should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or EA coding under the same v0 hypothesis.
