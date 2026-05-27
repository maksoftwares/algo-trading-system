# Phase 1 Cost Lifecycle Row Note

Overall status: REVIEW_NOTE

Generated at UTC: 2026-05-27

## Purpose

This note clarifies historical `COST_SUSPENDED` rows in Phase 1 dry-run logs after the measured-cost freshness audit reset the authoritative measured-cost clock.

## Current Authoritative State

| Field | Value |
| --- | --- |
| Current breakout family lifecycle | `COST_REVALIDATION_PENDING` |
| Current measured cost model | PENDING |
| Fresh observed market days | 1 / 5 |
| Authoritative fresh rows | 11,305 |
| Measured-cost revalidation | PENDING |
| Phase 2 execution eligibility | BLOCKED |

## Historical Rows

`PHASE1_DRY_RUN_LOG_REPORT.md` currently includes historical block reasons:

| Block reason | Count |
| --- | ---: |
| `COST_REVALIDATION_PENDING` | 3 |
| `COST_SUSPENDED` | 7 |

The `COST_SUSPENDED` rows are legacy diagnostic rows from before the freshness-aware measured-cost admission rule became authoritative. They must not be interpreted as a final post-freshness cost suspension decision.

## Rule Going Forward

`COST_SUSPENDED` may only become authoritative after all of the following are true:

1. `MEASURED_COST_MODEL.md` is PASS.
2. `cost_model_measured.csv` is generated from admitted `tick_fresh=true` weekday rows.
3. Measured-cost revalidation is rerun against that measured model.
4. Measured-cost revalidation returns FAIL or net expectancy falls below the pre-committed floor.

Until those conditions are true, the correct lifecycle is:

```text
COST_REVALIDATION_PENDING
```

## Phase Boundary

This note preserves historical rows. It does not rewrite logs, does not restart MT5, and does not authorize paper-mode or live execution.
