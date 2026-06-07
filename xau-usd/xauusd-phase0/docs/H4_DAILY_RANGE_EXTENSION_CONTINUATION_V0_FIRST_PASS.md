# H4 Daily Range Extension Continuation v0 First Pass

Date: 2026-06-07
Status: REJECTED_FIRST_PASS
Expert: `h4_daily_range_extension_continuation_v0`
Hypothesis SHA256: `87be45ad314d029e43ed0c892e63e336df1436d6f19f2896f639de4281e59ecd`

## Decision

Reject v0 without tuning.

The candidate produced ample trades in every matrix cell, but no cell reached PF >= 1.30. Capital.com was negative across costs, Pepperstone and Dukascopy were positive but below threshold, and concentration remains too high in several cells.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return % | Max Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Capital.com | best_case | 225 | 43.56% | 0.8725 | -3.95% | 1 |
| 2 | Capital.com | median | 225 | 43.56% | 0.8725 | -3.95% | 1 |
| 3 | Capital.com | p95 | 225 | 43.56% | 0.8602 | -4.35% | 1 |
| 4 | Pepperstone | best_case | 186 | 48.92% | 1.0837 | 2.05% | 1 |
| 5 | Pepperstone | median | 186 | 48.92% | 1.0837 | 2.05% | 1 |
| 6 | Pepperstone | p95 | 186 | 48.92% | 1.0794 | 1.95% | 1 |
| 7 | Dukascopy | best_case | 287 | 49.13% | 1.1745 | 5.76% | 0 |
| 8 | Dukascopy | median | 286 | 47.55% | 1.1268 | 4.17% | 0 |
| 9 | Dukascopy | p95 | 285 | 46.32% | 1.0752 | 2.50% | 0 |

## Gate Read

```text
PF >= 1.30 cells: 0/9
Trade-count cells >= 40 trades: 9/9
Max zero-trade months: 1
Cross-broker persistence: FAIL
First-pass decision: REJECTED_FIRST_PASS
```

## Interpretation

The paired continuation interpretation is better than the rejected reversal only in later broker windows, but it still lacks threshold-level PF and fails Capital.com materially. The H4 daily range-extension family should not be tuned in place.

Do not proceed with this candidate to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution. Any future revisit must be a materially different versioned hypothesis.
