# Phase 0 Independent Validation Status

Last updated: 2026-05-27

This document tracks the reviewer-requested D1-D4 checks. These checks do not change the current Phase 1 dry-run boundary, but they must be closed before Phase 2 paper-trading authorization.

## Summary

| Item | Status | Current conclusion |
| --- | --- | --- |
| D1 - Combinatorial Purged Cross-Validation | PASS | `breakout_retest` passed 135 purged chronological paths across all 9 matrix cells; pass rate 100%, median OOS PF 1.379, minimum OOS PF 1.135. |
| D2 - White Reality Check / SPA-style bootstrap | FAIL | Canonical fixed-notional monthly R rerun: `breakout_retest` remained the family winner against 66 non-empty matrix-ledger candidates, White Reality Check p-value 0.0002, and max pairwise SPA p-value 0.0174. The effective alpha tightened to 0.01 after the universe reached at least 30 candidates; same-family `round_number_retest_v0` and `symbol_normalized_round_retest_v0` failed pairwise SPA at that stricter threshold. |
| D3 - True 6-month holdout | PASS | The reserved period is configured, locked, the unlock file is absent, and `audit-true-holdout` found no generated result timestamps inside the 2025-07-01 to 2025-12-31 holdout window. |
| D4 - Independent Python reproduction | PASS | `breakout_retest` cell 2 was replayed by a standalone pandas event simulator and matched trade count, PF, win rate, total PnL, and max drawdown within the 5% tolerance. |

## D1 - Combinatorial Purged Cross-Validation

Command:

```powershell
.\.venv\Scripts\phase0.exe run-cpcv-validation --expert breakout_retest
```

Generated output:

```text
outputs/reports/PHASE0_CPCV_VALIDATION.md
outputs/reports/PHASE0_CPCV_PATHS.csv
outputs/manifests/PHASE0_CPCV_MANIFEST.json
```

Latest result:

| Metric | Value |
| --- | ---: |
| Status | PASS |
| Matrix cells tested | 9 |
| CPCV paths | 135 |
| Path pass rate | 100.0% |
| Median OOS PF | 1.379 |
| Minimum OOS PF | 1.135 |
| Minimum OOS trades | 2391 |

Interpretation:

The fixed `breakout_retest` definition stayed profitable across all purged chronological fold combinations. This supports robustness, but it does not replace Phase 1 soak completion or Phase 2 paper-trading drift evidence.

## D2 - White Reality Check / SPA-Style Bootstrap

Command:

```powershell
.\.venv\Scripts\phase0.exe run-reality-check --approved-expert breakout_retest --iterations 5000 --block-months 3 --max-pvalue 0.10
```

Generated output:

```text
outputs/reports/PHASE0_REALITY_CHECK.md
outputs/reports/PHASE0_REALITY_CHECK_SUMMARY.csv
outputs/manifests/PHASE0_REALITY_CHECK_MANIFEST.json
```

Latest result:

| Metric | Value |
| --- | ---: |
| Status | FAIL |
| Family winner | breakout_retest |
| White Reality Check p-value | 0.0002 |
| Max pairwise SPA p-value | 0.0174 |
| Effective accepted p-value | 0.01 |
| Non-empty candidate universe | 66 |
| Bootstrap iterations | 5000 |
| Circular block length | 3 months |

Canonicalization note:

The fixed-notional monthly R-series output is the canonical D2 evidence. Earlier percent-return or compounding variants are superseded because they can overweight account-path artifacts rather than the strategy's per-trade edge. Future D2 reruns should use the same fixed-notional R-series construction unless a reviewer explicitly approves a new pre-registered statistical method.

Current failure reason:

The expanded universe now has at least 30 non-empty candidates, so the D2 implementation tightens the effective accepted p-value from 0.10 to 0.01. `breakout_retest` remains the winner and the White Reality Check p-value remains strong, but pairwise SPA checks against same-family `round_number_retest_v0` and `symbol_normalized_round_retest_v0` fail the stricter 0.01 threshold. Treat D2 as an open blocker before Phase 2 authorization.

Method decision:

`docs/D2_METHOD_DECISION_2026_05_27.md` keeps the current fixed-notional candidate-level D2 report as the canonical Phase 2 readiness gate. It does not permit a retroactive PASS by collapsing same-family variants. It pre-registers a possible `D2_FAMILY_CLUSTERED_V0` study as a separate method candidate that must be reviewed before it can affect readiness.

Reviewer-facing note:

Any older D2 report or review comment that references percent-return compounding, dollar-account compounding, a smaller candidate universe, or a pre-threshold-tightening PASS is historical context only. The current D2 evidence is the fixed-notional monthly R-series rerun shown above.

Interpretation:

The approved expert remained the winner after a fixed-notional R rerun across the full non-empty tested matrix universe. The command reads every matrix-result directory with a usable trade ledger and keeps each expert as one monthly R series, so cost/broker cells do not become separate optimized candidates and raw dollar compounding artifacts do not drive the bootstrap. However, the expanded same-family search now blocks a clean D2 PASS under the stricter alpha rule. This does not invalidate the Phase 1 dry-run soak, but it must be resolved before Phase 2 authorization.

Related Review #3 gate-frequency audit:

```text
outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md
outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.csv
```

That audit now covers 67 candidates, with 64 rejected/research rows, 14 sample-size failures, 62 multi-cell expectancy failures, and no evidence that rejected v0 candidates should be rescued by frequency-bias assumptions alone.

Related Review #6 concentration-frequency audit:

```text
outputs/reports/PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md
outputs/reports/PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.csv
```

That audit adds normalized concentration ratios for concentration-failed candidates. It does not rescue or reclassify rejected candidates; it is context for future gate design if new low-frequency, pre-registered candidates are tested.

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
| Phase 2 paper trading | Blocked. D2 is now FAIL under the expanded-universe rule, and measured-cost, active-market soak, code-freeze, VPS, and owner approval gates are still not all PASS. |
| Live deployment | Blocked until dry-run soak, paper-trading evidence, and later operational gates are complete. |
