# EURUSD Neutral BLS release-time acceleration census verdict

## Verdict

`CENSUS_FAIL_NO_PNL_ALLOWED`

The exact event-entry family is closed without opening trade returns. The
point-in-time source, acceleration sign, 15-minute wait, Neutral ownership,
fixed execution, and sample gates were hash-locked and pushed first.

## Outcome-blind census

| Stage | Count |
|---|---:|
| Parsed initial releases | 267 |
| Missing/out-of-interval predecessors | 9 |
| Equal initial values | 14 |
| Directional release signals | 244 |
| Entry-time Neutral candidates | 30 |
| Candidate UTC dates | 30 |
| LONG / SHORT | 18 / 12 |

All three macro families survived the decision-time filters:

| Family | Neutral candidates |
|---|---:|
| CPI | 14 |
| PPI | 7 |
| NFP | 9 |

The chronological distribution was:

| Frozen window | Candidates | Required |
|---|---:|---:|
| 2019-2022 development | 19 | 20 |
| 2023 | 2 | 3 |
| 2024 | 1 | 3 |
| 2025 | 6 | 3 |
| 2026 H1 | 2 | 2 |
| Total | 30 | 40 |

The recent-half-year, both-side, and all-family gates passed. Total,
development, 2023, and 2024 capacity failed.

## Interpretation

The source itself has ample directional observations. Capacity is lost because
only 30 of 244 release-time signals are owned by the causal Neutral,
non-shock, non-compression state at the event entry. That is a regime/timing
intersection limitation, not a profit result.

No stop, target, or EURUSD path was loaded. Lowering the sample gates, changing
regime ownership, removing a family, or accepting the two-trade latest block
inside this exact contract would be post-census repair.

## Integrity

Deterministic census:

`outputs/neutral_bls_release_acceleration/CENSUS.json`

SHA-256:

`2aba83d11a26a6e4ebd562573e853355380df7ba0cc763de47e16057b3f5c74d`

No demo or live action is authorized.
