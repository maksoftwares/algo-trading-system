# Phase 3 Experimental Scope

Status: EXPERIMENTAL_ACTIVE

This document defines the experimental Phase 3 lane requested by the owner while Phase 2 evidence continues to mature.

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

The repo-side Phase 3 experiment is frozen after completion. New feature expansion is blocked unless the owner opens a new experimental ticket. Maintenance remains limited to bug fixes, report regeneration, consistency checks, and boundary documentation.

## Assumption

For design purposes only, this sandbox assumes:

```text
Phase 2 objective gates eventually pass.
```

That assumption is not written back into the real readiness reports. `PHASE2_READINESS_REPORT.md` remains the authority for the real project.

## Allowed Work

| Area | Allowed |
| --- | --- |
| Offline ledgers | Yes |
| Cost-survival simulation | Yes |
| Risk/kill-rule design | Yes |
| Promotion and rollback criteria | Yes |
| Docs and tests | Yes |
| MT5 deployment | No |
| Broker-action code | No |
| Live or paper account state changes | No |

## Inputs

| Input | Use |
| --- | --- |
| Phase 1 would-signal review CSV | Source of dry-run candidate events. |
| Phase 1 status summary | Confirms dry-run and permission boundary. |
| Phase 2 readiness report | Preserved as PENDING until real gates pass. |
| Measured-cost reports | Used only as context; no gate is force-passed here. |

## Outputs

| Output | Purpose |
| --- | --- |
| `PHASE3_EXPERIMENTAL_LEDGER.csv` | Offline event ledger built from already-blocked Phase 1 decisions. |
| `PHASE3_EXPERIMENTAL_SIMULATION.md` | Human-readable simulation summary. |
| `PHASE3_EXPERIMENTAL_STATUS.json` | Machine-readable status for the dashboard. |
| `PHASE3_EXPERIMENTAL_STATUS.md` | Reviewer-facing status summary. |
| `PHASE3_SUSPEND_FAMILY_REVIEW.md` | Review of cost-survival suspensions and whether they are primary events or duplicate observer rows. |
| `PHASE3_SUSPEND_FAMILY_ROWS.csv` | Filtered rows for each `SUSPEND_FAMILY` event with diagnosis fields. |
| `PHASE3_SUSPEND_FAMILY_DECISION.md` | Explicit keep-suspended decisions and future implementation rules for primary suspended events. |
| `PHASE3_COST_MODE_COMPARISON.md` | Comparison of entry-only, entry-exit, P95 fresh, and stress cost assumptions. |
| `PHASE3_COST_MODE_COMPARISON.csv` | Machine-readable cost-mode comparison. |
| `PHASE3_FAMILY_DEDUP_AUDIT.md` | Review-only classification of same-bar family groups. |
| `PHASE3_FAMILY_DEDUP_AUDIT.csv` | Machine-readable de-dup audit rows. |
| `PHASE3_PAPER_SHADOW_SUMMARY.md` | Side-experiment paper-shadow lifecycle summary; demo authorization remains false. |
| `PHASE3_PAPER_SHADOW_LEDGER.csv` | Offline paper-shadow rows showing eligible, cost-watch, blocked, duplicate, and conflict states. |
| `PHASE3_SHADOW_LIFECYCLE_SUMMARY.md` | Synthetic post-open lifecycle summary for would-open rows; not a backtest or paper trading. |
| `PHASE3_SHADOW_LIFECYCLE_LEDGER.csv` | Synthetic lifecycle rows with close reasons, net R, drawdown, and risk-lock states. |
| `PHASE3_LIFECYCLE_GUARD_SUMMARY.md` | Guarded controller comparison that blocks cost-watch, high-cost, and risk-locked synthetic exposure. |
| `PHASE3_LIFECYCLE_GUARD_LEDGER.csv` | Guarded lifecycle rows with block reasons, running equity, and daily/portfolio lock states. |
| `PHASE3_DEMO_REHEARSAL_CHECKLIST.md` | Non-deploying demo rehearsal checklist built from the guarded lifecycle. |
| `PHASE3_DEMO_REHEARSAL_LEDGER.csv` | Rehearsal event sequence for shadow open, shadow close, cost blocks, risk blocks, and no-exposure rows. |
| `PHASE3_COMPLETION_AUDIT.md` | Repo-side completion audit that separates finished Phase 3 prep from external demo/paper blockers. |
| `PHASE3_EXPERIMENTAL_SAFETY_REPORT.md` | Safety-boundary scan for broker-action references. |
| `PHASE3_EXPERIMENTAL_MANIFEST.md` | Source-hash manifest for inputs, scripts, status, and reports. |
| `PHASE3_EXPERIMENTAL_REVIEW_BUNDLE_LATEST.zip` | Portable review package for the experimental lane. |

## Family De-Duplication

| Stream | Role |
| --- | --- |
| `breakout_retest` | Primary stream. |
| `swing_breakout_retest_v0` | Observer-only same-family stream. |
| `symbol_normalized_round_retest_v0` | Observer-only same-family stream. |
| Provisional or disabled variants | Excluded from the experimental ledger. |

The ledger must expose `family_event_id`, `family_duplicate_group_id`, `family_event_role`, and `primary_stream_allowed` so reviewers can separate raw observer rows from unique family events.

## Cost Modes

| Mode | Meaning |
| --- | --- |
| `entry_only_proxy` | Entry spread plus entry slippage only. |
| `entry_exit_proxy` | Entry and exit spread plus entry and exit slippage. This is the default. |
| `p95_fresh_proxy` | Uses fresh measured P95 spread for both entry and exit spread assumptions. |
| `stress_2x_p95_proxy` | Doubles fresh measured P95 spread for both entry and exit stress. |

## State Strings

```text
EXPERIMENTAL_ACTIVE
EXPERIMENTAL_WAITING_FOR_PHASE2
EXPERIMENTAL_COST_SUSPEND_SCENARIO
EXPERIMENTAL_BOUNDARY_FAIL
EXPERIMENTAL_REVIEW_READY
EXPERIMENTAL_ARCHIVED
SIDE_EXPERIMENT_SYNTHETIC_LIFECYCLE_READY
SIDE_EXPERIMENT_GUARDED_LIFECYCLE_READY
SIDE_EXPERIMENT_DEMO_REHEARSAL_READY
```

## Non-Negotiable Boundary

If a future implementation is copied from this sandbox into the real system, it must first pass the real Phase 2 gates and go through a separate implementation review.
