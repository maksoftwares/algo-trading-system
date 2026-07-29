# EURUSD Neutral 06:00-08:00 UTC range-breakout transfer v1.1 census

Status: `CENSUS_PASS_EXECUTION_MAY_BE_SEPARATELY_LOCKED`

## Outcome-blind capacity

| Session signals | Neutral-owned signals | Fresh risk-eligible candidates | Active dates | Long | Short |
|---:|---:|---:|---:|---:|---:|
| 3,091 | 291 | 272 | 127 | 138 | 134 |

| Window | Candidates |
|---|---:|
| Development 2019-2022 | 155 |
| Validation 2023 | 18 |
| Validation 2024 | 31 |
| Pseudo-OOS 2025 | 55 |
| Pseudo-OOS 2026 H1 | 13 |
| Latest six months | 13 |

## Frozen gates

All eight outcome-blind capacity gates passed:

- total candidates: `PASS`
- distinct candidate dates: `PASS`
- development count: `PASS`
- each full OOS year: `PASS`
- 2026 H1 count: `PASS`
- each side: `PASS`
- latest six-month count: `PASS`
- maximum state-known lag: `PASS` at exactly 4.0 hours

The inherited v1 parent had 290 risk-eligible candidates. V1.1 excluded 18
stale candidates on six dates using the same four-hour limit frozen before
the first v1 count.

## Boundary

- Only completed M15 inputs, causal hourly regime state, timestamps, sides,
  and decision-time risk fields were loaded.
- No post-entry path, trade exit, EURUSD return, P&L, or oracle row was loaded.
- No performance gate was evaluated.
- A separate execution implementation and lock are required before outcome
  evaluation.
- No broker, demo, or live action occurred.
