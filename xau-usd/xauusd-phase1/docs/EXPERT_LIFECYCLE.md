# Expert Lifecycle

Expert states are versioned independently from the shell.

| State | Meaning |
| --- | --- |
| `DISABLED` | Expert cannot emit executable signals. |
| `RESEARCH_ONLY` | Expert may be logged as a hypothetical idea outside the shell. |
| `PHASE0_PENDING` | Automated evidence exists but manual or artifact gates remain open. |
| `DRY_RUN_APPROVED` | Expert may emit dry-run signals after final Phase 0 PASS. |
| `COST_SUSPENDED` | Historical evidence passed, but measured-cost revalidation failed; telemetry may continue, execution is blocked. |
| `DEMO_APPROVED` | Expert may enter demo pilot after dry-run validation. |
| `RETIRED` | Expert is blocked until a new version is researched. |

Current lifecycle:

| Expert | State | Reason |
| --- | --- | --- |
| `breakout_retest` | `COST_SUSPENDED` | Final Phase 0 PASS is superseded for execution by measured-cost revalidation FAIL; Phase 1 observation may continue only as telemetry. |
| `swing_breakout_retest_v0` | `DRY_RUN_APPROVED` | Research gates and Gate 9 passed; same-family with `breakout_retest`; Phase 1 observation only, not independent execution eligibility. |
| `trend_pullback` | `RETIRED` | Failed Phase 0 gates. |
| `range_mr` | `RETIRED` | Failed Phase 0 gates. |

The Phase 1 shell logs lifecycle state but does not override it.
