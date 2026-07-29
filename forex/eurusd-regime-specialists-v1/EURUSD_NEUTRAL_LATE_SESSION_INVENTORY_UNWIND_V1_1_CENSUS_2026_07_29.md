# EURUSD Neutral late-session inventory-unwind V1.1 census

Status: `CENSUS_PASS_EXECUTION_MAY_BE_SEPARATELY_LOCKED`

## Outcome-blind final ladder

| Displacement | Candidates | Development | 2023 | 2024 | 2025 | 2026 H1 | Long | Short | Latest 6m | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 6 pips | 63 | 33 | 8 | 3 | 10 | 9 | 26 | 37 | 9 | Fail: 2024 capacity |
| 4 pips | 89 | 49 | 11 | 5 | 15 | 9 | 38 | 51 | 9 | Pass |

The frozen rule selected the highest threshold passing every unchanged
capacity gate. Six pips failed only the five-candidate floor in 2024. Four
pips passed all eight gates and is permanently selected.

Across 1,512 complete inventory days, the selected threshold produced 273
confirmed unwind signals, 102 Neutral-owned signals, and 89 risk-eligible
candidates on 89 dates. Candidate state-known lag ranged from 2.25 to 3.25
hours, within the four-hour maximum.

## Boundary

- Only completed 20:00-23:55 and 00:00-00:10 UTC M5 inputs, causal hourly
  regime state, timestamps, sides, and decision-time risk fields were
  loaded.
- Threshold selection used candidate capacity only.
- No post-entry path, trade exit, EURUSD return, P&L, or oracle row was
  loaded.
- No performance gate was evaluated.
- The passing census permits only a separately implemented, tested,
  hash-locked execution using this exact candidate manifest.
- No broker, demo, or live action occurred.
