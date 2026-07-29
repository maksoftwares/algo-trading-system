# EURUSD Neutral prior-24-hour extreme fade census

Status: `CENSUS_PASS_EXECUTION_MAY_BE_SEPARATELY_LOCKED`

## Outcome-blind capacity

| Complete prior windows | Extreme signals | Neutral-owned | Risk-eligible | Active dates | Long | Short |
|---:|---:|---:|---:|---:|---:|---:|
| 1,507 | 586 | 210 | 196 | 196 | 93 | 103 |

| Window | Candidates |
|---|---:|
| Development 2019-2022 | 116 |
| Validation 2023 | 25 |
| Validation 2024 | 19 |
| Pseudo-OOS 2025 | 21 |
| Pseudo-OOS 2026 H1 | 15 |
| Latest six months | 15 |

All eight frozen capacity gates passed. Candidate state-known lag ranged
from two to four hours, within the four-hour maximum.

## Boundary

- Only fully completed prior-24-hour M5 windows, causal hourly regime state,
  timestamps, sides, and decision-time risk fields were loaded.
- No post-entry path, trade exit, EURUSD return, P&L, or oracle row was loaded.
- No performance gate was evaluated.
- A separate execution implementation and lock are required before outcome
  evaluation.
- No broker, demo, or live action occurred.
