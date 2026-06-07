# H4 BTC Risk Pressure Gold Reversal v2 First Pass

Date: 2026-06-07
Status: REJECTED_FIRST_PASS
Expert: `h4_btc_risk_pressure_gold_reversal_v2`
Hypothesis SHA256: `3d10bfef2cf3c9a0325a172bb93c390015a6ff76461db1fd5f53cf9685d48edc`

## Decision

Reject v2 without tuning.

The candidate tried to sit between sparse high-PF v0 and broader weaker v1. It did not recover a valid BTC edge: Pepperstone reached PF >= 1.30, but Capital.com stayed below threshold, Dukascopy was materially negative, and every cell stayed below the 40-trade minimum.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return % | Max Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 21 | 38.10% | 1.1528 | 0.62% | 5 |
| 2 | Capital.com | median | 21 | 38.10% | 1.1528 | 0.62% | 5 |
| 3 | Capital.com | p95 | 21 | 38.10% | 1.0420 | 0.17% | 5 |
| 4 | Pepperstone | best_case | 19 | 57.89% | 1.4770 | 1.43% | 6 |
| 5 | Pepperstone | median | 19 | 57.89% | 1.4770 | 1.43% | 6 |
| 6 | Pepperstone | p95 | 19 | 57.89% | 1.4650 | 1.40% | 6 |
| 7 | Dukascopy | best_case | 13 | 15.38% | 0.3636 | -1.79% | 8 |
| 8 | Dukascopy | median | 13 | 15.38% | 0.3659 | -1.74% | 8 |
| 9 | Dukascopy | p95 | 13 | 15.38% | 0.3514 | -1.83% | 8 |

## Gate Read

```text
PF >= 1.30 cells: 3/9
Trade-count cells >= 40 trades: 0/9
Max zero-trade months: 8
Cross-broker persistence: FAIL
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

The stricter intermediate variant did not solve the original sparse-evidence problem and also lost the all-broker PF persistence seen in v0. This BTC stress-reversal family remains a clue, not an approval-worthy EA.

Do not proceed with v2 to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution. Any continuation must be a genuinely new versioned hypothesis with a materially different reason to expect broader, broker-persistent activity.
