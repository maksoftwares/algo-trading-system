# Phase 3 Observer Conflict Playbook

Status: REVIEW_READY_EXPERIMENTAL

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

## Purpose

The current Phase 3 de-duplication audit shows `0` observer conflicts and all current multi-row groups classify as `TRUE_DUPLICATE`. This playbook defines what to do if future would-signal data produces conflicts.

## Classifications

| Classification | Meaning | Required response |
| --- | --- | --- |
| `TRUE_DUPLICATE` | Same family, same bar, same direction, materially same execution. | Collapse to one family event. |
| `SAME_BAR_DISTINCT_LEVEL` | Same bar but different level source or level price. | Review only; do not auto-promote. |
| `SAME_BAR_DIRECTION_CONFLICT` | Same bar but opposing direction. | Block family event and require review. |
| `SAME_BAR_EXECUTION_CONFLICT` | Same bar/direction but materially different entry, stop, target, or stop distance. | Block or route to review; do not duplicate exposure. |

## Review Fields

Every conflict review should record:

| Field | Required |
| --- | --- |
| `family_event_id` | yes |
| `bar_time` | yes |
| `observers` | yes |
| `directions` | yes |
| `level_kinds` | yes |
| `level_prices` | yes |
| `entry_prices` | yes |
| `stop_losses` | yes |
| `take_profits` | yes |
| `stop_distance_points` | yes |
| `review_decision` | yes |
| `reviewer` | yes |
| `reviewed_at_utc` | yes |

## Allowed Decisions

| Decision | Meaning |
| --- | --- |
| `COLLAPSE_DUPLICATE` | Treat as one family event. |
| `BLOCK_CONFLICT` | Do not produce a paper-shadow event. |
| `KEEP_PRIMARY_ONLY` | Use `breakout_retest` primary row only, observer rows remain metadata. |
| `REQUIRES_NEW_SPEC` | The event pattern is outside the current design. |

## Boundary

This playbook does not authorize demo or broker execution. It only prevents the future system from treating same-family observer rows as independent opportunities.
