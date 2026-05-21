# Expert Lifecycle

Expert states are versioned independently from the shell.

| State | Meaning |
| --- | --- |
| `DISABLED` | Expert cannot emit executable signals. |
| `RESEARCH_ONLY` | Expert may be logged as a hypothetical idea outside the shell. |
| `PHASE0_PENDING` | Automated evidence exists but manual or artifact gates remain open. |
| `DRY_RUN_APPROVED` | Expert may emit dry-run signals after final Phase 0 PASS. |
| `DEMO_APPROVED` | Expert may enter demo pilot after dry-run validation. |
| `RETIRED` | Expert is blocked until a new version is researched. |

Current lifecycle:

| Expert | State | Reason |
| --- | --- | --- |
| `breakout_retest` | `PHASE0_PENDING` | Gate 9 manual adversarial review is incomplete. |
| `trend_pullback` | `RETIRED` | Failed Phase 0 gates. |
| `range_mr` | `RETIRED` | Failed Phase 0 gates. |

The Phase 1 shell logs lifecycle state but does not override it.
