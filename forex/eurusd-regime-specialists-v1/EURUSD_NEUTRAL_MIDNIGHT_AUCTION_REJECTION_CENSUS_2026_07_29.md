# EURUSD Neutral midnight-auction rejection census

Status: `CENSUS_FAIL_NO_PNL_ALLOWED`

## Outcome-blind capacity

| Complete auctions | Rejection signals | Neutral-owned | Risk-eligible | Active dates | Long | Short |
|---:|---:|---:|---:|---:|---:|---:|
| 1,948 | 103 | 29 | 18 | 18 | 13 | 5 |

| Window | Candidates |
|---|---:|
| Development 2019-2022 | 13 |
| Validation 2023 | 2 |
| Validation 2024 | 0 |
| Pseudo-OOS 2025 | 2 |
| Pseudo-OOS 2026 H1 | 1 |
| Latest six months | 1 |

## Frozen gates

- `minimum_risk_eligible_candidates_total`: `FAIL`
- `minimum_distinct_candidate_dates_total`: `FAIL`
- `minimum_candidates_development_2019_2022`: `FAIL`
- `minimum_candidates_each_full_oos_year`: `FAIL`
- `minimum_candidates_pseudo_oos_2026h1`: `FAIL`
- `minimum_candidates_each_side`: `FAIL`
- `minimum_recent_six_month_candidates`: `FAIL`
- `maximum_candidate_state_known_lag_hours`: `PASS`

Candidate state-known lag ranged from 2.25 to 3.25 hours, within the
four-hour maximum. Capacity failed everywhere else: the strict three-bar
midnight rejection was too rare to support chronological evaluation.

## Boundary

- Only the completed 00:00, 00:05, and 00:10 UTC M5 bars, the exact 00:15
  entry quote, causal hourly regime state, timestamps, sides, and
  decision-time risk fields were loaded.
- No post-entry path, trade exit, EURUSD return, P&L, or oracle row was
  loaded.
- No performance gate was evaluated.
- The execution and performance stages are prohibited.
- The exact family is retired without relaxing its thresholds.
- No broker, demo, or live action occurred.
