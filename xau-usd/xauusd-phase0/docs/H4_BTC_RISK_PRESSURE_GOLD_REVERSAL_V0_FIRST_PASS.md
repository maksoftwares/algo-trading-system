# H4 BTC Risk Pressure Gold Reversal v0 First Pass

Date: 2026-06-07
Status: REJECTED_FIRST_PASS_SPARSE_PF_LEAD
Expert: `h4_btc_risk_pressure_gold_reversal_v0`
Hypothesis SHA256: `9a2f7de27da89a214346bbd79a3ed2fd7376c2c1ee22105db0c616a6c515964f`

## Decision

Reject v0 without tuning.

The candidate is a useful research lead because all 9 matrix cells reached PF >= 1.30, including p95 cost cells and all three broker windows. It fails the first-pass approval gate because every cell is far below the 40-trade minimum.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return % | Max DD % | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 14 | 42.86% | 1.8716 | 1.69% | 0.91% | 8 |
| 2 | Capital.com | median | 14 | 42.86% | 1.8716 | 1.69% | 0.91% | 8 |
| 3 | Capital.com | p95 | 14 | 42.86% | 1.8426 | 1.65% | 0.91% | 8 |
| 4 | Pepperstone | best_case | 10 | 60.00% | 1.6632 | 1.24% | 0.88% | 6 |
| 5 | Pepperstone | median | 10 | 60.00% | 1.6632 | 1.24% | 0.88% | 6 |
| 6 | Pepperstone | p95 | 10 | 60.00% | 1.6164 | 1.16% | 0.88% | 6 |
| 7 | Dukascopy | best_case | 9 | 33.33% | 1.4899 | 0.52% | 1.05% | 8 |
| 8 | Dukascopy | median | 9 | 33.33% | 1.3993 | 0.45% | 1.09% | 8 |
| 9 | Dukascopy | p95 | 9 | 33.33% | 1.4526 | 0.48% | 1.03% | 8 |

## Gate Read

```text
PF >= 1.30 cells: 9/9
Trade-count cells >= 40 trades: 0/9
Max zero-trade months: 8
First-pass decision: REJECTED_FIRST_PASS_SPARSE_PF_LEAD
```

## Interpretation

BTC-USD daily stress plus H4 XAU reversal timing is the strongest BTC-related lead so far, but v0 is not approval-worthy because the evidence is too sparse and activity fails. It must not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution under the v0 hypothesis.

The only acceptable continuation is a new versioned hypothesis written and hash-locked before testing, with broader mechanical activity and the same no-tuning boundary.
