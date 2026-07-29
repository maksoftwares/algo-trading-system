# EURUSD Neutral rates/dollar sign-consensus H4 census

Status: `REJECTED_OUTCOME_BLIND_CAPACITY_CENSUS`

## Outcome-blind capacity

| Total Neutral signals | Active dates | Long | Short |
|---:|---:|---:|---:|
| 62 | 57 | 32 | 30 |

| Window | Signals |
|---|---:|
| DEVELOPMENT_2019_2022 | 23 |
| OOS_2023 | 15 |
| OOS_2024 | 12 |
| OOS_2025 | 11 |
| OOS_2026_H1 | 1 |
| LATEST_SIX_MONTHS | 1 |

## Frozen gates

- `minimum_neutral_signals_total`: `PASS`
- `minimum_neutral_signals_development`: `PASS`
- `minimum_neutral_signals_each_full_oos_year`: `PASS`
- `minimum_neutral_signals_recent_half_year`: `FAIL`
- `minimum_neutral_signals_each_side`: `PASS`

## Boundary

- Only completed H4 inputs, lagged daily context, timestamps, sides, and causal regime ownership were counted.
- No post-entry path, stop, target, P&L, or oracle match was evaluated.
- No threshold, direction, hour, date, or regime was selected after viewing an outcome.
- No broker, demo, or live action occurred.
