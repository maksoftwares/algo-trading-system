# Phase 1 Reporting Policy

Last updated: 2026-05-22

## Purpose

Phase 1 generated many reports quickly because the dry-run shell was being expanded and reviewed slice by slice. That was useful during buildout. For ongoing review, the project should converge on a smaller canonical surface.

## Canonical Reports

| Artifact | Purpose |
| --- | --- |
| `outputs/reports/PHASE1_STATUS_SUMMARY.json` | Machine-readable single source of truth for automation and dashboards. |
| `outputs/reports/PHASE1_ACCEPTANCE_REPORT.md` | Human-readable gate report for Phase 1 acceptance. |
| `outputs/review_bundles/PHASE1_DRY_RUN_BUNDLE_*.zip` | Third-party review package containing the evidence set. |

## Derived Reports

These reports may still be generated on demand or included inside review bundles, but they should not become separate decision authorities:

- `PHASE1_DRY_RUN_LOG_REPORT.md`
- `PHASE1_SOAK_DRIFT_REPORT.md`
- `PHASE1_WOULD_SIGNAL_REPORT.md`
- `PHASE1_WOULD_SIGNAL_REVIEW.csv`
- `PHASE1_RUNTIME_HEALTH_REPORT.md`
- `PHASE1_SOAK_HISTORY.csv`
- `PHASE1_SOAK_HISTORY_REPORT.md`
- `PHASE1_REVIEW_INDEX.md`
- `PHASE2_READINESS_REPORT.md`

## Rule

If reports disagree, the canonical order is:

1. `PHASE1_STATUS_SUMMARY.json`
2. `PHASE1_ACCEPTANCE_REPORT.md`
3. Latest review bundle manifest
4. Derived report that explains the underlying check

Phase 1 remains dry-run only regardless of report status. A passing report does not authorize broker-side behavior by itself.

Static docs must not pin current runtime row counts, latest bar times, soak percentages, active-streak hours, or acceptance status. Those values move during soak and belong in `PHASE1_STATUS_SUMMARY.json`.
