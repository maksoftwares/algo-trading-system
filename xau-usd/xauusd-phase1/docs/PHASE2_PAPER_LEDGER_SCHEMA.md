# Phase 2 Paper Ledger Schema

This schema is preparation only. It defines the paper-mode evidence contract that can be used only after Phase 1 acceptance, corrected measured-cost revalidation PASS, and explicit project-owner approval.

## Boundary

- The ledger records paper-only projections from already-blocked dry-run decisions.
- The source decision row must remain `dry_run=true`.
- The source decision row must remain `trade_permission=false`.
- The ledger must never change broker state, account state, or platform positions.
- The ledger is valid only for review and cost-measurement evidence.

## Required Columns

| Column | Required | Type | Source | Validation |
| --- | --- | --- | --- | --- |
| event_id | yes | string | paper ledger | Unique stable event id. |
| paper_session_id | yes | string | paper ledger | Stable for one paper-mode run. |
| source_run_id | yes | string | decision_log.csv | Must match source `run_id`. |
| source_decision_row_number | yes | integer | decision_log.csv | One-based source row number. |
| timestamp_broker | yes | datetime | decision_log.csv | Broker timestamp from source row. |
| timestamp_utc | yes | datetime | decision_log.csv | UTC timestamp from source row. |
| timestamp_local | yes | datetime | decision_log.csv | Local timestamp from source row. |
| symbol | yes | string | decision_log.csv | Must match approved symbol. |
| expert_family | yes | string | policy | `breakout_retest_family` for current approved family. |
| expert | yes | string | decision_log.csv | Source observer or future paper expert id. |
| observer | yes | string | decision_log.csv | Source observer lane. |
| decision_bar_time | yes | datetime | decision_log.csv | Source `bar_time`. |
| paper_event_type | yes | enum | paper ledger | `WOULD_OPEN`, `WOULD_CLOSE`, `STATE_UPDATE`, or `BLOCKED`. |
| paper_state | yes | enum | paper ledger | `PAPER_FLAT`, `PAPER_OPEN`, `PAPER_CLOSED`, or `PAPER_BLOCKED`. |
| direction | yes | enum | decision_log.csv | `LONG`, `SHORT`, or `NONE`. |
| level_kind | yes | string | decision_log.csv | Source level type. |
| level_price | yes | decimal | decision_log.csv | Source level price. |
| entry_price_projected | yes | decimal | decision_log.csv | Source projected entry. |
| stop_price_projected | yes | decimal | decision_log.csv | Source projected stop. |
| target_price_projected | yes | decimal | decision_log.csv | Source projected target. |
| stop_distance_points | yes | decimal | decision_log.csv | Source projected stop distance. |
| risk_pct_requested | yes | decimal | risk policy | Requested paper risk percentage. |
| risk_pct_allowed | yes | decimal | risk policy | Allowed risk after lock checks. |
| risk_state | yes | enum | decision_log.csv | Source risk state. |
| spread_points | yes | decimal | decision_log.csv | Source spread. |
| slippage_points_assumed | yes | decimal | paper fill model | Assumed paper slippage. |
| modeled_cost_R | yes | decimal | Phase 0 baseline | Modeled baseline all-in cost in R. |
| measured_cost_R | yes | decimal | Phase 2 measurement | Measured paper cost proxy in R. |
| net_expectancy_R_baseline | yes | decimal | Phase 0 baseline | Baseline net expectancy in R. |
| net_expectancy_R_after_measured_cost | yes | decimal | Phase 2 measurement | Viability metric after measured costs. |
| execution_state | yes | enum | decision_log.csv | Source execution state. |
| news_state | yes | enum | decision_log.csv | Source news state. |
| router_regime | yes | enum | decision_log.csv | Source regime/router state. |
| session | yes | enum | decision_log.csv | Source session state. |
| trade_permission | yes | boolean | decision_log.csv | Must remain `false` at source. |
| dry_run | yes | boolean | decision_log.csv | Must remain `true` at source. |
| block_reason | yes | string | decision_log.csv | Source blocked reason. |
| kill_rule_state | yes | enum | paper policy | `NORMAL`, `COST_WATCH`, `SUSPEND_FAMILY`, or `MANUAL_LOCK`. |
| review_status | yes | enum | reviewer | `PENDING`, `REVIEWED`, `ACCEPTED`, or `REJECTED`. |
| review_notes | yes | string | reviewer | Human notes for event review. |

## Minimum Controls

- `net_expectancy_R_after_measured_cost` must be compared against `+0.15R`.
- If the breakout-retest family falls below the threshold, `kill_rule_state` becomes `SUSPEND_FAMILY`.
- `swing_breakout_retest_v0` and `breakout_retest` remain one correlated edge family for risk and kill-rule purposes.
- `breakout_retest` is currently cost-suspended; it becomes the only possible execution-eligible paper expert only if corrected measured-cost revalidation passes. `swing_breakout_retest_v0` remains observer-only telemetry.
- Paper-mode output must preserve the source `decision_log.csv` row number so reviewers can reconstruct every event.
- Paper-mode output must be reproducible from a saved `decision_log.csv` without needing broker access.

## Generated Evidence

The machine-checkable schema report is:

```text
outputs/reports/PHASE2_PAPER_LEDGER_SCHEMA_REPORT.md
```

The generated column template is:

```text
outputs/reports/PHASE2_PAPER_LEDGER_COLUMNS.csv
```
