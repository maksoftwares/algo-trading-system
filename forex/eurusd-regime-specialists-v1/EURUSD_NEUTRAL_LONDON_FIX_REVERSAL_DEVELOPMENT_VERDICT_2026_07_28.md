# EURUSD Neutral London-fix reversal development verdict

## Verdict

`REJECTED_IN_DEVELOPMENT_FORWARD_FORBIDDEN`

The frozen post-fix reversal mechanism failed before chronological forward
evaluation. No 2023, 2024, 2025, or 2026 trade outcome was opened, and no
latest-six-month P&L was calculated for this family.

## Lock and census

The rule, DST conversion, two expert definitions, rolling prior-only
threshold, confirmation, execution, tests, and evaluation order were committed
and pushed in `81d62fa4` before the census.

The outcome-blind census passed:

| Item | Count |
|---|---:|
| Neutral dates | 642 |
| Raw fix observations | 642 |
| Confirmed candidates | 165 |
| Candidate dates | 165 |
| Ordinary-fix candidates | 150 |
| Month-end candidates | 15 |
| LONG / SHORT | 98 / 67 |
| 2019-2020 | 45 |
| 2021-2022 | 52 |
| 2023 | 20 |
| 2024 | 16 |
| 2025 | 20 |
| 2026 H1 | 12 |

All frozen census gates passed. This authorized development outcomes only.

## Development evidence

### Ordinary fix

| Window | Trades | Win rate | Payoff | PF | Net R |
|---|---:|---:|---:|---:|---:|
| 2019-2020 | 43 | 32.56% | 1.454 | 0.702 | -8.81 |
| 2021-2022 | 50 | 26.00% | 1.454 | 0.511 | -18.44 |
| Combined | 93 | 29.03% | 1.454 | 0.595 | -27.25 |

Combined maximum drawdown was 30.56R. One candidate exceeded the frozen
25-pip risk ceiling; there were no missing entries or position-overlap skips.

### Month-end fix

Only three development trades executed: one in 2019-2020 and two in
2021-2022. Combined win rate was 33.33%, payoff 1.461, PF 0.731, and net
-0.55R. It failed both the minimum sample and profitability gates.

## Interpretation

The 1.5R structure delivered the intended payoff, but the confirmed reversal
side was wrong too often. Ordinary-fix win rate deteriorated from 32.56% to
26.00% across the two development blocks. This is an economic failure, not a
cost-only near miss.

Reversing the direction, lowering the displacement threshold, deleting a
side, selecting month-end subperiods, or opening favorable forward years would
be post-outcome repair and is prohibited.

The exact family is closed. The selection ledger contains no expert, states
`forward_outcomes_loaded: false`, and the implementation exposes no forward
command.

## Evidence hashes

- Outcome-blind census:
  `a3d5b0c60d43a3fe60af0679045444e4897de45e235502b81bf6bd45de954cd2`.
- Candidate ledger:
  `52156b93f14a9b08f2eb5a455ad0c63997c85a1aebee2717524ba036a80bd28f`.
- Development result:
  `5101e7344ef0a4ed0b45120ec6b7f219785272062282090c6ad1ddb3d1268ac1`.
- Empty selection:
  `33e90844ef7684d527f9efadf140ce71fe2fed0c443684506d49e64a9818f4f8`.
- Ordinary-fix development trades:
  `b29c85302deddea2531a3a2a5d67ed00d51b9a15e0152f9f2f155620dcb6d561`.
- Month-end development trades:
  `181dd85d00b4dbca622a6f518516d6bc5ad26c55a02d9188906dbd0a63ea70b4`.

No broker action is authorized.
