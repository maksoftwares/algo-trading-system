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
| `COST_SUSPENDED_CANONICAL_PENDING_SANITY_CHECK` | Measured-cost revalidation failed and canonical execution is blocked while the cost-conversion sanity check is still pending. |
| `COST_SUSPENDED_CANONICAL` | Measured-cost revalidation failed and the sanity check confirmed the conversion path; canonical execution is blocked for this family. |
| `COST_REVALIDATION_REGENERATED_PENDING_REVIEW` | A cost-model bug was found and fixed; regenerated cost evidence needs reviewer sign-off before eligibility can change. |
| `DEMO_APPROVED` | Expert may enter demo pilot after dry-run validation. |
| `DEMO_REPAIR_PREFLIGHT_PENDING` | Owner-approved demo repair lane exists, but combined preflight and owner packet must pass before arming. |
| `RETIRED` | Expert is blocked until a new version is researched. |

Current lifecycle:

| Expert | State | Reason |
| --- | --- | --- |
| `breakout_retest` | `COST_SUSPENDED_CANONICAL` | Fresh measured-cost model is PASS, measured-cost revalidation is FAIL, assumption delta is FAIL, and `MEASURED_COST_REVALIDATION_SANITY_CHECK.md` is `CALCULATION_CONFIRMED`. Phase 1 observation may continue only as telemetry. |
| `swing_breakout_retest_v0` | `COST_SUSPENDED_CANONICAL` | Research gates and Gate 9 passed; same-family with `breakout_retest`; it inherits the breakout-retest family measured-cost suspension and is not independent execution eligibility. |
| `symbol_normalized_round_retest_v0` | `COST_SUSPENDED_CANONICAL` | Same-family level-and-retest candidate; it inherits the family-level measured-cost suspension and is not independent execution eligibility. |
| `quarter_round_retest_v0` | `COST_SUSPENDED_CANONICAL` | Same-family level-and-retest candidate; provisional research evidence cannot override the family-level measured-cost suspension. |
| `round_number_retest_v0` | `COST_SUSPENDED_CANONICAL` | Same-family level-and-retest candidate; provisional research evidence cannot override the family-level measured-cost suspension. |
| `session_extreme_retest_v0` | `COST_SUSPENDED_CANONICAL` | Same-family level-and-retest candidate; provisional research evidence cannot override the family-level measured-cost suspension. |
| `a3_round_retest_guarded_v1` | `DEMO_REPAIR_PREFLIGHT_PENDING` | EA-T1 A3-only repair lane, magic `933000`, dry-run committed default, requires combined preflight and owner packet before any demo arming. |
| `a3_round_retest_structured_v1` | `DEMO_REPAIR_PREFLIGHT_PENDING` | EA-T2 A3-only structural repair lane, magic `933100`, dry-run committed default, requires combined preflight and owner packet before any demo arming. |
| `a3_session_extreme_repair_tbd` | `RESEARCH_ONLY` | EA-T3 does not exist; magic band `933200-933299` is reserved pending T14 forensics and separate pre-registration. |
| `trend_pullback` | `RETIRED` | Failed Phase 0 gates. |
| `range_mr` | `RETIRED` | Failed Phase 0 gates. |

The Phase 1 shell logs lifecycle state but does not override it. Cost state is family-level for `breakout_retest`, `swing_breakout_retest_v0`, `symbol_normalized_round_retest_v0`, `round_number_retest_v0`, `session_extreme_retest_v0`, and any future level-and-retest family member.
