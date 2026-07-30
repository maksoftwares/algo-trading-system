# EURUSD dense residual regime-family result

Date: 2026-07-30

Status: **HISTORICAL_VALIDATION_REJECTED**

Demo-order authorization: **false**

## What is stopping the portfolio

The remaining problem is not data access, execution plumbing, or the ability
to generate trades. It is the absence of a stable directional edge on the
weekdays not already traded by the protected M15 expert.

The protected M15 component remains valid at 0.2031 trades per weekday, PF
1.4105, stressed PF 1.3405, and best-5%-removed PF 1.1068. Reaching the
0.85/day admission floor still requires roughly 0.65 independent trades per
weekday.

This preregistered experiment deliberately tested whether five causal regimes
could supply those missing trades. Twelve simple direction rules were frozen
before their rule-level results were inspected. Each regime selected one rule
using only 2016-07-01 through 2021-12-31; 2022-01-01 through 2026-06-30 was
locked validation.

## Regime result

| Regime | Development selection | Locked-validation result |
|---|---|---:|
| Cross-pair compression | No robust rule; cash | No trade |
| Broad EUR up | 60-minute strength fade | -10.6125R |
| Broad EUR down | 240-minute strength fade | -8.3000R |
| Short/long disagreement | Insufficient development sample; cash | No trade |
| Mixed transition | No robust after-cost rule; cash | No trade |

The two development-selected trend experts reversed out of sample. Together
they produced 140 validation trades:

- 0.1195 trades per weekday;
- 36.43% wins and 1.3561 payoff;
- PF 0.7771, stressed PF 0.6941;
- best-5%-removed PF 0.6544;
- trade-sequence half PFs 0.7871 and 0.7669;
- net result -18.9125R.

This is direct evidence of concept drift. Relaxing the development gate would
increase activity, but the large Compression and Mixed-Transition opportunity
pools already had their best development rules below stressed PF 1.0. Admitting
them would manufacture frequency by adding negative expectancy.

## Two-year combined broker window

Only 44 dense-residual trades fell inside the protected M15 broker window, and
they lost 5.6125R before the M15 profits were added.

| Metric | Combined two years | Latest 12 months |
|---|---:|---:|
| Trades | 150 | 79 |
| Trades per weekday | 0.2874 | 0.3027 |
| Weekday coverage | 27.20% | 28.35% |
| Win rate | 46.00% | 45.57% |
| Payoff | 1.5652 | 1.6391 |
| Profit factor | 1.3333 | 1.3723 |
| Stressed profit factor | 1.2592 | 1.2990 |
| Best-5%-removed PF | 0.9956 | 1.0500 |
| Net P&L | $57.11 | $35.26 |

The combined PF is positive because the protected M15 component supplies the
profits. It does not validate the residual component. The 0.287/day result is
0.563/day below the 0.85 admission floor and 0.713/day below the desired
one-trade-per-weekday operating point.

## Correct next move

Do not weaken the gates or deploy these two static experts. The next bounded
test must address the observed drift directly: an online, prior-outcomes-only
regime router that can switch among the already frozen side rules without
using the current outcome. It must trade densely enough to test the economic
question, and it must still be rejected if its residual PF, stress PF, winner
concentration, or chronological stability fails.

Historical results remain research evidence only. A successful retrospective
candidate would still require a newly frozen live publisher, exact MT5 quote
and outcome parity, and forward demo soak before orders.

## Reproducibility

Run:

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_dense_residual_family.py
```

Preregistered implementation hashes:

- config:
  `530d30fb6f6dad6f530b5c7d567c0055a4f37d7aa1b19e3b63db21be5a2e9c7e`
- source:
  `c96aaea62c5f7453f3a3afa07d0e114c1c575615920ba660ab199ff163122db2`

Output hashes:

- `DEVELOPMENT_CANDIDATES.csv`:
  `c54faa7b4dbe068c4230a90636f591477b5dc30b113f8146cd719194d7b88428`
- `VALIDATION_TRADES.csv`:
  `afc820744b4c111b0d42fbd0b0152e9cf6843916a491feddb395265b746b95da`
- `MONTHLY.csv`:
  `4ffb17ed832a8a6f0103b141d64462c7dd93127ed855cf288ca18a6be4d32810`
- `RESULT.json`:
  `978d33d18a8a2b3653a94a4faeb634422dfe35deae08c3d4498f3060052f1044`
- `RESULT.md`:
  `4bd10a78a092aed6082b02c0015103011ec67154fdcdffdfd60c0e8bed6790c2`
