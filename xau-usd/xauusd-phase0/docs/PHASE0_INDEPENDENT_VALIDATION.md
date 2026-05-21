# Phase 0 Independent Validation Status

Last updated: 2026-05-22

This document tracks the reviewer-requested D3 and D4 checks. These checks do not change the current Phase 1 dry-run boundary, but they must be closed before Phase 2 paper-trading authorization.

## Summary

| Item | Status | Current conclusion |
| --- | --- | --- |
| D3 - True 6-month holdout | PASS | The reserved period is configured, locked, the unlock file is absent, and `audit-true-holdout` found no generated result timestamps inside the 2025-07-01 to 2025-12-31 holdout window. |
| D4 - Independent Python reproduction | PASS | `breakout_retest` cell 2 was replayed by a standalone pandas event simulator and matched trade count, PF, win rate, total PnL, and max drawdown within the 5% tolerance. |

## D3 - True Holdout

Configured holdout:

| Field | Value |
| --- | --- |
| Config file | `config/true_holdout_period.yaml` |
| Status | `reserved` |
| Start | `2025-07-01T00:00:00Z` |
| End | `2025-12-31T23:59:59Z` |
| Required unlock file | `docs/FINAL_HOLDOUT_UNLOCK_APPROVAL.md` |
| Required CLI flag | `--unlock-true-holdout` |
| Unlock file present locally | `false` |

Latest run-context evidence:

| Field | Value |
| --- | --- |
| Manifest | `outputs/manifests/PHASE0_RUN_CONTEXT.json` |
| `true_holdout_unlocked` | `false` |
| `true_holdout_unlock_file_present` | `false` |
| `true_holdout_overlap_detected` | `true` |
| `normal_workflows_policy` | `blocked_or_trimmed_unless_unlock_file_and_cli_flag_are_present` |

Completed audit:

```powershell
.\.venv\Scripts\phase0.exe audit-true-holdout
```

Generated output:

```text
outputs/reports/PHASE0_TRUE_HOLDOUT_AUDIT.md
outputs/manifests/PHASE0_TRUE_HOLDOUT_AUDIT_MANIFEST.json
```

Latest audit result:

| Check | Status | Evidence |
| --- | --- | --- |
| true_holdout_enabled | PASS | True holdout guard is enabled. |
| unlock_file_absent | PASS | `docs/FINAL_HOLDOUT_UNLOCK_APPROVAL.md` is absent. |
| run_context_locked | PASS | Run context remains locked. |
| result_rows_exclude_holdout | PASS | 96 result CSV files scanned; no holdout-window timestamps found. |
| latest_result_boundary | PASS | Latest audited result timestamp is `2025-06-30T23:55:00+00:00`, before holdout start. |

Interpretation:

The configured periods overlap the holdout calendar, but the generated result rows are trimmed before the holdout starts and the unlock controls remain closed. D3 is closed for the current evidence package.

## D4 - Independent Python Reproduction

Completed target:

| Field | Value |
| --- | --- |
| Expert | `breakout_retest` |
| Suggested cell | `capital_com` / `median` |
| Source artifact | `outputs/matrix_results/breakout_retest/cell_2_breakout_retest_capital_com_median_trades.csv` |
| Reference report | `outputs/reports/phase0_breakout_retest_results.md` |
| Tolerance | Profit factor and trade count within 5% unless a documented simulator difference explains the variance. |

Generated output:

```text
outputs/reports/PHASE0_INDEPENDENT_REPRODUCTION.md
outputs/manifests/PHASE0_INDEPENDENT_REPRODUCTION_MANIFEST.json
```

Command:

```powershell
.\.venv\Scripts\phase0.exe generate-independent-reproduction --expert breakout_retest --cell-id 2 --tolerance-pct 5
```

Latest result:

| Metric | Reference | Independent | Delta % | Status |
| --- | ---: | ---: | ---: | --- |
| trade_count | 7287 | 7287 | 0.0 | PASS |
| profit_factor | 1.4119615864693404 | 1.4119615864693404 | 0.0 | PASS |
| win_rate | 0.4844243172773432 | 0.4844243172773432 | 0.0 | PASS |
| total_pnl_usd | 18642279.988449715 | 18642279.988449715 | 0.0 | PASS |
| max_drawdown_pct | 9.812749721579038 | 9.81274972157902 | 0.000000000000181 | PASS |

The reproduction uses a standalone pandas event replay and does not call the Phase 0 strategy class, execution simulator, or metrics module.

## Current Go / No-Go Effect

| Milestone | Effect |
| --- | --- |
| Phase 1 dry-run shell | Not blocked. Phase 1 has no broker-side execution and is telemetry-only. |
| Phase 2 paper trading | Still blocked by five-day dry-run soak completion, owner approval, and remaining advanced validation decisions. D3 and D4 are closed. |
| Live deployment | Blocked until dry-run soak, paper-trading evidence, and later operational gates are complete. |
