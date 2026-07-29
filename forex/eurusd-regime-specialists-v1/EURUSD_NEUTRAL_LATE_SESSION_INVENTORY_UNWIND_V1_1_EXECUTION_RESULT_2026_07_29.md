# EURUSD Neutral late-session inventory-unwind V1.1 execution result

Status: `REJECTED_EXACT_LATE_SESSION_INVENTORY_UNWIND`

## Frozen result

| Trades | Wins | Win rate | Realized payoff | PF | Net | Max drawdown |
|---:|---:|---:|---:|---:|---:|---:|
| 89 | 33 | 37.08% | 1.470 | 0.867 | -7.52R | 20.34R |

The 1.5R design delivered the intended payoff ratio, but not the required
45-55% win rate or PF of at least 1.15.

## Chronological windows

| Window | Trades | Win rate | Payoff | PF | Net |
|---|---:|---:|---:|---:|---:|
| Development 2019-2022 | 49 | 28.57% | 1.482 | 0.593 | -14.23R |
| 2023 | 11 | 36.36% | 1.456 | 0.832 | -1.20R |
| 2024 | 5 | 60.00% | 1.446 | 2.169 | +2.39R |
| 2025 | 15 | 53.33% | 1.454 | 1.662 | +4.72R |
| 2026 H1 / latest six months | 9 | 44.44% | 1.443 | 1.155 | +0.79R |

The recent three-window improvement is reported but not activated after
inspection. Development and 2023 are genuine failures, and the favorable
2024 sample contains only five trades.

## Robustness and sides

- Long: 38 trades, 28.95% wins, PF 0.592, -11.22R.
- Short: 51 trades, 43.14% wins, PF 1.128, +3.70R.
- Extra 0.5-pip round-trip cost: PF 0.742, -15.84R.
- Best 5% of winners removed: PF 0.734, -14.97R.
- Overall maximum drawdown: 20.34R versus the frozen 15R ceiling.

The short side and recent years are not selected after outcome inspection.

## Regime 1 oracle resemblance

- Exact same-side matches: 32; precision 35.96%; recall 1.22%.
- Same-side matches within 15 minutes: 75; precision 84.27%; recall 2.87%.

This is the strongest resemblance feature of the rule, but it does not
overcome negative full-history expectancy. The oracle selected only future
winners, whereas the causal expert cannot know which of its highly similar
entries will reach target before stop.

## Decision

The exact four-pip inventory-unwind family is retired. Threshold, direction,
confirmation, year, side, and volatility subgroup repairs are prohibited.
No broker, demo, or live action occurred.
