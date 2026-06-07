# H1 Volatility Expansion Pullback Continuation v0 First Pass

Date: 2026-06-07
Status: REJECTED_FIRST_PASS
Expert: `h1_volatility_expansion_pullback_continuation_v0`
Hypothesis SHA256: `799e420b745e142487f9eec44e6ac1e3050fec07e674440a0ff96a311256a715`

## Decision

Reject v0 without tuning.

The candidate produced enough trades in every matrix cell, but it did not show a cost-adjusted edge. No cell reached PF >= 1.30, Capital.com and Pepperstone were negative across costs, and the small Dukascopy best-case positive result stayed far below threshold.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return % | Max Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 73 | 38.36% | 0.8793 | -2.57% | 1 |
| 2 | Capital.com | median | 73 | 38.36% | 0.8793 | -2.57% | 1 |
| 3 | Capital.com | p95 | 73 | 38.36% | 0.8543 | -3.12% | 1 |
| 4 | Pepperstone | best_case | 66 | 36.36% | 0.8326 | -3.19% | 1 |
| 5 | Pepperstone | median | 66 | 36.36% | 0.8326 | -3.19% | 1 |
| 6 | Pepperstone | p95 | 66 | 36.36% | 0.8230 | -3.39% | 1 |
| 7 | Dukascopy | best_case | 77 | 41.56% | 1.0157 | 0.33% | 1 |
| 8 | Dukascopy | median | 77 | 41.56% | 0.9622 | -0.79% | 1 |
| 9 | Dukascopy | p95 | 77 | 41.56% | 0.9298 | -1.47% | 1 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Max zero-trade months: 1
Cross-broker persistence: FAIL
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

High-volatility pullback continuation is active enough and structurally cheap enough to test, but this fixed definition has no robust edge. The result is especially weak because the two earlier broker windows are negative across all cost models.

Do not proceed with this candidate to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution. Any future volatility-expansion work must use a new versioned hypothesis with a materially different mechanism.
