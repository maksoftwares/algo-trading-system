# EURUSD Neutral prior-24-hour extreme fade execution result

Status: `REJECTED_EXACT_PRIOR24_EXTREME_FADE`

## Primary result

| Trades | Wins | Win rate | Realized payoff | PF | Net R | Max drawdown |
|---:|---:|---:|---:|---:|---:|---:|
| 196 | 81 | 41.33% | 0.929 | 0.654 | -36.737 | 39.435R |

The rule did not reach the requested approximately 50% win rate, 1.5
realized payoff, or profitable PF.

## Chronology

| Window | Trades | Win rate | Payoff | PF | Net R |
|---|---:|---:|---:|---:|---:|
| Development 2019-2022 | 116 | 44.83% | 0.909 | 0.738 | -15.850 |
| OOS 2023 | 25 | 32.00% | 0.864 | 0.407 | -8.738 |
| OOS 2024 | 19 | 52.63% | 0.951 | 1.057 | +0.427 |
| OOS 2025 | 21 | 19.05% | 1.269 | 0.299 | -11.111 |
| OOS 2026 H1 / latest six months | 15 | 46.67% | 0.924 | 0.808 | -1.465 |

The isolated positive 2024 slice cannot be selected after outcome.

## Direction and robustness

| Slice | Trades | Win rate | Payoff | PF | Net R |
|---|---:|---:|---:|---:|---:|
| Long | 93 | 39.78% | 0.887 | 0.586 | -21.593 |
| Short | 103 | 42.72% | 0.966 | 0.720 | -15.144 |
| Extra 0.5-pip stress | 196 | 40.82% | 0.891 | 0.614 | -42.321 |
| Top 5% removed | 186 | 38.17% | 0.832 | 0.514 | -51.700 |

## Oracle resemblance

| Match | Matches | Precision | Recall |
|---|---:|---:|---:|
| Exact timestamp and side | 74 | 37.76% | 2.83% |
| Same side within 15 minutes | 113 | 57.65% | 4.32% |

The causal rule passed both frozen resemblance gates and materially improved
behavioral similarity. It still failed the economic, chronological, side,
drawdown, and robustness gates.

## Verdict

This exact signal and lifecycle are retired. No clock, direction,
close-location threshold, body threshold, risk, hold, side, weekday, year,
or subgroup was changed after the result opened.

The result is research evidence only and cannot authorize demo or live
trading. No broker action occurred.
