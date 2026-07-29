# EURUSD Neutral H4 Walk-Forward Result

Status: `REJECTED_H4_NEUTRAL_WALKFORWARD`

## Outcome

The fixed monthly past-only model achieved the intended asymmetric payoff, but not enough directional accuracy to produce a profitable Regime 1 system.

| Scope | Trades | Win rate | Payoff | PF | Stressed PF | Net R | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full 2020-2026 H1 walk-forward | 120 | 37.50% | 1.470 | 0.882 | 0.848 | -8.91 | 13.72R |
| Latest 12 months | 3 | 66.67% | 1.487 | 2.975 | 2.852 | +1.99 | 1.01R |
| Latest 6 months | 2 | 100.00% | N/A | infinite | infinite | +2.99 | 0.00R |

The recent result is only two 2026 trades and cannot override the losing full history.

## Chronology

| Window | Trades | Win rate | Payoff | PF | Net R |
|---|---:|---:|---:|---:|---:|
| 2020-2021 | 29 | 27.59% | 1.490 | 0.568 | -9.12 |
| 2022-2023 | 64 | 43.75% | 1.489 | 1.158 | +5.71 |
| 2024-2025 | 25 | 28.00% | 1.365 | 0.531 | -8.49 |
| 2026 H1 | 2 | 100.00% | N/A | infinite | +2.99 |

The run built 14,300 symmetric side-candidates, selected 172 before position-overlap control, rejected 52 overlaps, and executed 120 trades. It passed sample, payoff, recent numerical, and drawdown gates. It failed win rate, full PF, stressed PF, chronological stability, positive-active-month, and winner-concentration gates.

## Decision

Close this exact slow H4 macro/price walk-forward family without probability-threshold, feature, side, year, training-length, stop, or target retuning. The evidence says the unresolved Regime 1 problem is signal accuracy, not payoff engineering or model capacity. No demo or broker action is authorized.
