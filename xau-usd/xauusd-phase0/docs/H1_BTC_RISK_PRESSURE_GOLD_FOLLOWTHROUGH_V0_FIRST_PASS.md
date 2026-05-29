# H1 BTC Risk Pressure Gold Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_btc_risk_pressure_gold_followthrough_v0`
Hypothesis SHA256: `77c0ce190ea3affb71ab3cbfca2e5aa3d20645cb7ad331a540b334884e0f4422`

## Decision

Reject v0 without tuning.

The candidate introduced a new BTC-USD daily risk-pressure data class and reached the 40-trade floor in all 9 cells. It failed the first-pass edge gate because 0/9 cells reached PF >= 1.30 and every broker window was net negative.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 80 | 40.00% | 0.9004 | -2.17% | 4.31% | 0 |
| 2 | Capital.com | median | 80 | 40.00% | 0.9004 | -2.17% | 4.31% | 0 |
| 3 | Capital.com | p95 | 80 | 40.00% | 0.8767 | -2.70% | 4.58% | 0 |
| 4 | Pepperstone | best_case | 55 | 40.00% | 0.9156 | -1.26% | 3.75% | 0 |
| 5 | Pepperstone | median | 55 | 40.00% | 0.9156 | -1.26% | 3.75% | 0 |
| 6 | Pepperstone | p95 | 55 | 40.00% | 0.8968 | -1.55% | 3.89% | 0 |
| 7 | Dukascopy | best_case | 51 | 37.25% | 0.8174 | -2.61% | 4.96% | 0 |
| 8 | Dukascopy | median | 51 | 37.25% | 0.7975 | -2.88% | 5.16% | 0 |
| 9 | Dukascopy | p95 | 51 | 37.25% | 0.7593 | -3.46% | 5.58% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Total cost-cell trades: 558
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

BTC-USD daily risk pressure is genuinely independent of the retest family, but this fixed safe-haven follow-through interpretation has no cost-adjusted edge across the broker matrix. It should not proceed to deciles, Gate 9, Phase 1 observation, Phase 2, or tuning under the same v0 hypothesis.
