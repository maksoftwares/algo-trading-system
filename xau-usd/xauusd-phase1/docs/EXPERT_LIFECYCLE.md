# Expert Lifecycle

Expert states are versioned independently from the shell.

| State | Meaning |
| --- | --- |
| `DISABLED` | Expert cannot emit executable signals. |
| `RESEARCH_ONLY` | Expert may be logged as a hypothetical idea outside the shell. |
| `PHASE0_PENDING` | Automated evidence exists but manual or artifact gates remain open. |
| `DRY_RUN_APPROVED` | Expert may emit dry-run signals after final Phase 0 PASS. |
| `COST_REVALIDATION_PENDING` | Historical evidence passed, but the authoritative fresh measured-cost model or revalidation is not complete; telemetry may continue, execution is blocked. |
| `COST_SUSPENDED` | Historical evidence passed, but authoritative measured-cost revalidation failed; telemetry may continue, execution is blocked. |
| `DEMO_APPROVED` | Expert may enter demo pilot after dry-run validation. |
| `RETIRED` | Expert is blocked until a new version is researched. |

Current lifecycle:

| Expert | State | Reason |
| --- | --- | --- |
| `breakout_retest` | `COST_REVALIDATION_PENDING` | Final Phase 0 PASS is execution-blocked until fresh measured-cost model PASS and measured-cost revalidation PASS. Phase 1 observation may continue only as telemetry. |
| `swing_breakout_retest_v0` | `COST_REVALIDATION_PENDING` | Research gates and Gate 9 passed; same-family with `breakout_retest`; it inherits the breakout-retest family measured-cost state and is not independent execution eligibility. |
| `trend_pullback` | `RETIRED` | Failed Phase 0 gates. |
| `range_mr` | `RETIRED` | Failed Phase 0 gates. |

The Phase 1 shell logs lifecycle state but does not override it. Cost state is family-level for `breakout_retest`, `swing_breakout_retest_v0`, `symbol_normalized_round_retest_v0`, `round_number_retest_v0`, `session_extreme_retest_v0`, and any future level-and-retest family member.
