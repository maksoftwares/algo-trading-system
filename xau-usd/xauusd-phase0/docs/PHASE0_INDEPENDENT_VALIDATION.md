# Phase 0 Independent Validation Status

Last updated: 2026-05-22

This document tracks the reviewer-requested D3 and D4 checks. These checks do not change the current Phase 1 dry-run boundary, but they must be closed before Phase 2 paper-trading authorization.

## Summary

| Item | Status | Current conclusion |
| --- | --- | --- |
| D3 - True 6-month holdout | GUARDED / NEEDS INDEPENDENT AUDIT | The reserved period is configured, locked, and the unlock file is absent. The run context also reports that available local data overlaps the reserved calendar period, so a final audit must confirm those rows were blocked or trimmed by workflow policy. |
| D4 - Independent Python reproduction | PENDING | No separate reproduction report is committed yet. At least one `breakout_retest` matrix cell must be reproduced independently and compared within the accepted tolerance. |

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

Interpretation:

The overlap flag means the local data store contains coverage that reaches the reserved calendar window. That is expected for a live research machine with broker history exports, but it is not enough by itself to prove the holdout stayed untouched. The required final D3 audit is:

1. Confirm no unlock file exists.
2. Confirm no command was run with the unlock flag.
3. Confirm the result manifests and result rows exclude the reserved period unless a signed unlock exists.
4. Record the command output and hashes in the final review bundle.

Until that audit is completed, D3 remains guarded rather than fully satisfied.

## D4 - Independent Python Reproduction

Required target:

| Field | Value |
| --- | --- |
| Expert | `breakout_retest` |
| Suggested cell | `capital_com` / `median` |
| Source artifact | `outputs/matrix_results/breakout_retest/cell_2_breakout_retest_capital_com_median_trades.csv` |
| Reference report | `outputs/reports/phase0_breakout_retest_results.md` |
| Tolerance | Profit factor and trade count within 5% unless a documented simulator difference explains the variance. |

Required output:

```text
outputs/reports/PHASE0_INDEPENDENT_REPRODUCTION.md
outputs/manifests/PHASE0_INDEPENDENT_REPRODUCTION_MANIFEST.json
```

The reproduction should use a small standalone event simulator that does not call the Phase 0 strategy/backtester entry points. It may reuse CSV readers and generic metric formulas only if the report states exactly which shared helpers were reused.

## Current Go / No-Go Effect

| Milestone | Effect |
| --- | --- |
| Phase 1 dry-run shell | Not blocked. Phase 1 has no broker-side execution and is telemetry-only. |
| Phase 2 paper trading | Blocked until D3 and D4 are explicitly closed or owner signs a documented exception. |
| Live deployment | Blocked until D3, D4, dry-run soak, paper-trading evidence, and later operational gates are complete. |
