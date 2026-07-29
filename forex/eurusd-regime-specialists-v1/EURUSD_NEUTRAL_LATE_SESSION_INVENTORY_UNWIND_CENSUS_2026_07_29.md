# EURUSD Neutral late-session inventory-unwind census

Status: `CENSUS_FAIL_NO_PNL_ALLOWED`

## Outcome-blind threshold ladder

| Displacement | Candidates | Development | 2023 | 2024 | 2025 | 2026 H1 | Long | Short | Latest 6m |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 pips | 21 | 16 | 0 | 0 | 3 | 2 | 5 | 16 | 2 |
| 10 pips | 32 | 23 | 0 | 0 | 4 | 5 | 12 | 20 | 5 |
| 8 pips | 46 | 26 | 5 | 2 | 5 | 8 | 16 | 30 | 8 |

The frozen rule required the highest threshold passing every capacity gate.
None passed, so the 8-pip table is retained only as the most inclusive
failure record. Across 1,512 complete inventory days, that version produced
136 confirmed unwind signals, 54 Neutral-owned signals, and 46 risk-eligible
dates.

## Frozen gates at 8 pips

- `minimum_risk_eligible_candidates_total`: `FAIL`
- `minimum_distinct_candidate_dates_total`: `FAIL`
- `minimum_candidates_development_2019_2022`: `FAIL`
- `minimum_candidates_each_full_oos_year`: `FAIL`
- `minimum_candidates_pseudo_oos_2026h1`: `PASS`
- `minimum_candidates_each_side`: `PASS`
- `minimum_recent_six_month_candidates`: `PASS`
- `maximum_candidate_state_known_lag_hours`: `PASS`

Candidate state-known lag ranged from 2.25 to 3.25 hours. The decisive
coverage defect was 2024, which contained only two candidates against the
frozen five-candidate minimum.

## Boundary

- Only completed 20:00-23:55 and 00:00-00:10 UTC M5 inputs, causal hourly
  regime state, timestamps, sides, and decision-time risk fields were
  loaded.
- Threshold selection used candidate capacity only.
- No post-entry path, trade exit, EURUSD return, P&L, or oracle row was
  loaded.
- No performance gate was evaluated.
- Execution is prohibited for this exact 12/10/8-pip ladder.
- No broker, demo, or live action occurred.
