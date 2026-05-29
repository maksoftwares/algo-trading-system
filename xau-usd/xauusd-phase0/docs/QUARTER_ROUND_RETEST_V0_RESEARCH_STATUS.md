# Quarter Round Retest v0 Research Status

Generated: 2026-05-29
Status: `PROVISIONAL_PASS_PENDING_GATE9`

## Decision

`quarter_round_retest_v0` is the first new candidate in this hunt to clear the automated research path. It is selected as a provisional future EA candidate pending manual Gate 9 adversarial review.

This candidate is same-family with the approved breakout/round-number retest family. It is not independent diversification.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Zero months |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | capital_com | best_case | 6184 | 49.05% | 1.4456 | 94592.36% | 0 |
| 2 | capital_com | median | 6184 | 49.05% | 1.4456 | 94592.36% | 0 |
| 3 | capital_com | p95 | 6184 | 49.05% | 1.3051 | 17994.99% | 0 |
| 4 | pepperstone | best_case | 8507 | 49.18% | 1.5250 | 1442727.42% | 0 |
| 5 | pepperstone | median | 8507 | 49.18% | 1.5250 | 1442727.42% | 0 |
| 6 | pepperstone | p95 | 8507 | 49.18% | 1.4333 | 333451.56% | 0 |
| 7 | dukascopy | best_case | 9786 | 49.80% | 1.5234 | 12837750.80% | 0 |
| 8 | dukascopy | median | 9786 | 49.80% | 1.5234 | 12837750.80% | 0 |
| 9 | dukascopy | p95 | 9786 | 49.80% | 1.4678 | 2974946.04% | 0 |

## Automated Gate Snapshot

| Gate | Result |
|---|---|
| PF >= 1.30 in at least 7/9 cells | PASS, 9/9 |
| At least 40 trades per cell | PASS, 9/9 |
| Max zero-trade months <= 3 | PASS, max 0 |
| Cost sensitivity | PASS by p95 PF retention |
| Decile persistence | PASS, 10/10 deciles PF > 1.0 |
| Multisymbol transfer | PASS, EURUSD PF 1.3548, USDJPY PF 1.4607 |
| Intrabar ambiguity | PASS context, 330/73431 ambiguous exits, 0.45%, adverse-first PF 1.5160 |
| Gate 9 adversarial review | PENDING, 0/119 sampled losing trades reviewed |

## Decile Summary

| Decile | Trades | PF |
|---:|---:|---:|
| 1 | 2363 | 1.5097 |
| 2 | 1865 | 1.3198 |
| 3 | 1705 | 1.4033 |
| 4 | 2002 | 1.5644 |
| 5 | 3118 | 1.3809 |
| 6 | 3008 | 1.3352 |
| 7 | 2922 | 1.3774 |
| 8 | 2949 | 1.3529 |
| 9 | 2993 | 1.4913 |
| 10 | 4286 | 1.6790 |

## Required Manual Gate 9

Review file:

```text
outputs/adversarial_review/quarter_round_retest_v0_losing_trades_review.csv
```

Current score:

```text
PENDING
Reviewed: 0/119
Logic gaps: 0
Logic-gap pct: n/a
```

To become a fully approved future EA candidate, the 119 sampled losing trades must be reviewed and logic-gap failures must remain <=25%.
