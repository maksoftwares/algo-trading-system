# EURUSD Neutral 06:00-08:00 UTC range-breakout transfer census

Status: `CENSUS_FAIL_NO_PNL_ALLOWED`

## Outcome-blind capacity

| Session signals | Neutral-owned signals | Risk-eligible candidates | Active dates | Long | Short |
|---:|---:|---:|---:|---:|---:|
| 3,091 | 291 | 290 | 132 | 151 | 139 |

| Window | Candidates |
|---|---:|
| Development 2019-2022 | 173 |
| Validation 2023 | 18 |
| Validation 2024 | 31 |
| Pseudo-OOS 2025 | 55 |
| Pseudo-OOS 2026 H1 | 13 |
| Latest six months | 13 |

## Frozen gates

- `minimum_risk_eligible_candidates_total`: `PASS`
- `minimum_distinct_candidate_dates_total`: `PASS`
- `minimum_candidates_development_2019_2022`: `PASS`
- `minimum_candidates_each_full_oos_year`: `PASS`
- `minimum_candidates_pseudo_oos_2026h1`: `PASS`
- `minimum_candidates_each_side`: `PASS`
- `minimum_recent_six_month_candidates`: `PASS`
- `maximum_candidate_state_known_lag_hours`: `FAIL`

The maximum state-known lag was 86.5 hours against the frozen four-hour limit.

## Freshness diagnosis

This diagnosis uses only timestamps and pre-entry candidate fields.

- Eighteen candidates on six dates exceeded four hours of state staleness.
- All 18 were in 2019, including weekend carry and isolated source gaps.
- Applying the already-declared four-hour freshness boundary as a diagnostic
  eligibility filter would leave 272 candidates on 127 dates: 138 long and
  134 short.
- That diagnostic subset is not an admitted candidate and no outcome was
  opened. Any revision must be separately specified, hash-locked, committed,
  and pushed before another census.

## Boundary

- Only completed M15 inputs, causal hourly regime state, timestamps, sides,
  and decision-time risk fields were loaded.
- No post-entry path, trade exit, EURUSD return, P&L, or oracle row was loaded.
- No performance gate was evaluated.
- The execution and performance stages remain prohibited.
- No broker, demo, or live action occurred.
