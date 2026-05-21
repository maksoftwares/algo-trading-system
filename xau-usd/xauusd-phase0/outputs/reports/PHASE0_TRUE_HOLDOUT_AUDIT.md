# Phase 0 True Holdout Audit

Overall status: PASS

## Holdout Window

| Field | Value |
| --- | --- |
| start | 2025-07-01T00:00:00+00:00 |
| end | 2025-12-31T23:59:59+00:00 |
| latest_result_timestamp_utc | 2025-06-30T23:55:00+00:00 |
| scanned_result_csv_files | 96 |

## Checks

| Check | Status | Message |
| --- | --- | --- |
| true_holdout_enabled | PASS | True holdout guard is enabled in phase0.yaml. |
| unlock_file_absent | PASS | Unlock file is absent: docs\FINAL_HOLDOUT_UNLOCK_APPROVAL.md |
| run_context_locked | PASS | Run context remains locked. Configured periods overlap the holdout calendar, so result rows were audited for trimming. |
| result_rows_exclude_holdout | PASS | No holdout-window timestamps found in 96 scanned result CSV file(s). |
| latest_result_boundary | PASS | Latest audited result timestamp is 2025-06-30T23:55:00+00:00, before holdout start 2025-07-01T00:00:00+00:00. |

## Overlap Findings

No holdout-window result rows found.

## Interpretation

A PASS means generated result artifacts exclude the reserved holdout window and the unlock controls remain closed. It does not unlock the holdout for future testing.
