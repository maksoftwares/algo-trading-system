# H1 BTC Risk Pressure Gold Reversal v0 First Pass

Date: 2026-06-07
Status: REJECTED_FIRST_PASS
Expert: `h1_btc_risk_pressure_gold_reversal_v0`
Hypothesis SHA256: `66e35019ca40f9205da9f48dfd924eb8b9ff07a665b35efa23ea0bf1c459cd48`

## Decision

Reject v0 without tuning.

The candidate tested a fresh H1 reversal version of the BTC stress idea. It did not produce a viable EA candidate: no matrix cell reached PF >= 1.30, no matrix cell reached the 40-trade minimum, Capital.com and Pepperstone were negative across costs, and the only positive pocket was sparse Dukascopy below threshold.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return % | Max Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 26 | 38.46% | 0.9455 | -0.31% | 6 |
| 2 | Capital.com | median | 26 | 38.46% | 0.9455 | -0.31% | 6 |
| 3 | Capital.com | p95 | 26 | 38.46% | 0.9159 | -0.48% | 6 |
| 4 | Pepperstone | best_case | 18 | 33.33% | 0.6580 | -1.49% | 8 |
| 5 | Pepperstone | median | 18 | 33.33% | 0.6580 | -1.49% | 8 |
| 6 | Pepperstone | p95 | 18 | 33.33% | 0.6467 | -1.55% | 8 |
| 7 | Dukascopy | best_case | 10 | 60.00% | 1.2094 | 0.39% | 13 |
| 8 | Dukascopy | median | 10 | 60.00% | 1.0567 | 0.10% | 13 |
| 9 | Dukascopy | p95 | 10 | 60.00% | 0.9421 | -0.11% | 13 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 0/9
Max zero-trade months: 13
Cross-broker persistence: FAIL
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

Moving the BTC stress-reversal idea down to H1 did not solve the evidence problem. It reduced activity versus the target and removed the strong all-cell PF seen in sparse H4 v0.

Do not proceed with this candidate to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution. Any BTC continuation needs a materially different data or mechanism, not another minor threshold variant.
