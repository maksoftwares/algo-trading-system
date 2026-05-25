# Phase 2 Authorization Checklist

Last updated: 2026-05-25

This checklist separates work that is already closed from gates that still require wall-clock evidence or explicit owner approval. Phase 2 remains paper-mode preparation only until every required gate below is closed.

## Closed Evidence

| Item | Status | Evidence |
| --- | --- | --- |
| Phase 0 final verdict | PASS | `breakout_retest` is approved; `swing_breakout_retest_v0` and `symbol_normalized_round_retest_v0` are approved same-family future expert candidates. |
| D1 CPCV | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_CPCV_VALIDATION.md` |
| D2 Reality Check / SPA-style bootstrap | PASS | Canonical fixed-notional monthly R rerun against 29 non-empty matrix-ledger candidates: White p=0.0002, max SPA p=0.0188; percent-return/compounding variants are superseded; `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REALITY_CHECK.md` |
| D3 true holdout audit | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_TRUE_HOLDOUT_AUDIT.md` |
| D4 independent reproduction | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_INDEPENDENT_REPRODUCTION.md` |
| Same-family second candidate | PASS | `xau-usd/xauusd-phase0/docs/SWING_BREAKOUT_RETEST_V0_GATE9_REVIEW.md` |
| Rejected-candidate gate audit | PASS | Latest audit: 53 audited candidates, 50 rejected/research rows, 9 sample-size failures, 48 multi-cell expectancy failures; `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md` |
| Frequency-normalized concentration audit | PASS | Latest audit: 53 audited candidates, 48 absolute concentration failures, 47 normalized review-context candidates; it does not rescue rejected candidates and is review context only; `xau-usd/xauusd-phase0/outputs/reports/PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md` |
| Diversification availability finding | PASS | Twelve non-level H4/D1/W1 candidates plus additional H1 intermarket and volatility-regime candidates were hash-locked and rejected first-pass; current operating frame remains single-edge; `xau-usd/xauusd-phase0/docs/DIVERSIFICATION_AVAILABILITY_FINDING.md` |
| Forward hypothesis gates | PASS | `docs/HYPOTHESIS_LOCKING.md` pre-registers normalized concentration thresholds and a Pepperstone+Dukascopy cross-venue PF floor for future candidates. |
| Phase 1 dry-run compile | PASS | `C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log` |
| Phase 1 source safety | PASS | `scripts/audit_phase1_safety.py` |
| Phase 1 runtime health | PASS | `outputs/reports/PHASE1_RUNTIME_HEALTH_REPORT.md` |
| Phase 1 would-signal evidence | PASS | `outputs/reports/PHASE1_WOULD_SIGNAL_REPORT.md` |
| Fixed-notional cost report | PASS | `xau-usd/xauusd-phase0/outputs/reports/FIXED_NOTIONAL_REPORT.md` |
| Passive spread logger deployment | PASS | Deployed, compiled, and producing logs in the isolated logger clone; `xau-usd/xauusd-phase0/outputs/reports/PASSIVE_SPREAD_LOGGER_DEPLOYMENT.md` |
| Phase 2 cost-measurement protocol | PASS | `docs/PHASE2_COST_MEASUREMENT_PROTOCOL.md` documents Phase 2 as a cost-measurement experiment and pre-commits the +0.15R suspension rule. |
| Single-edge risk plan | PASS | `docs/PHASE2_SINGLE_EDGE_RISK_PLAN.md` treats same-family variants as one correlated breakout-retest family and makes `breakout_retest` the only execution-eligible first paper stream. |
| External health monitor | PASS | `docs/PHASE2_OPERATIONS_PREP.md` defines the out-of-terminal monitor and local scheduler-friendly check script. |
| Disaster recovery runbook | PASS | `docs/PHASE2_OPERATIONS_PREP.md` documents recovery assets, procedure, and rollback rule. |
| Capital allocation ladder | PASS | `docs/PHASE2_SINGLE_EDGE_RISK_PLAN.md` defines the paper-to-micro ladder and single-edge sizing constraint. |
| Quarterly/review triggers | PASS | `docs/PHASE2_SINGLE_EDGE_RISK_PLAN.md` defines cost, trade-count, PF, drawdown, concentration, execution, and logic triggers. |

## Still Pending

| Gate | Current status | Closure rule |
| --- | --- | --- |
| Five trading day soak | PENDING | `PHASE1_ACCEPTANCE_REPORT.md` must show five-day soak PASS. |
| Active-market 72-hour soak | PENDING | `PHASE1_ACCEPTANCE_REPORT.md` and `PHASE1_STATUS_SUMMARY.json` must show longest active-market bar-continuity streak >= 72h with no dry-run, permission, schema, or server-time violations. Weekend closures break this active-market streak. |
| Process/code-freeze 96-hour gate | PENDING | `PHASE1_ACCEPTANCE_REPORT.md` and `PHASE1_STATUS_SUMMARY.json` must show process uptime streak >= 96h and code-freeze hours >= 96h using `phase1_code_freeze_started_at.txt`. |
| Measured cost model | PENDING | `xau-usd/xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md` must show PASS. |
| Measured-cost revalidation | PENDING | `xau-usd/xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` must show PASS. |
| Phase 1 review index | PENDING | `PHASE1_REVIEW_INDEX.md` must show PASS after acceptance and bundle refresh. |
| Phase 2 readiness report | PENDING | `PHASE2_READINESS_REPORT.md` must show PASS. |
| Project owner approval | PENDING | Use `docs/PHASE2_OWNER_APPROVAL_TEMPLATE.md` after all objective gates pass, then add `outputs/reports/PHASE2_OWNER_APPROVAL.md` only when the owner explicitly authorizes paper-mode work. |
| VPS selection | PENDING | `docs/PHASE2_VPS_SELECTION_MATRIX.md` must show `Overall status: PASS` after provider, region, specs, backup access, and monitoring approach are selected. |
| Non-level/intermarket forcing candidate run | PASS | Twelve non-level H4/D1/W1 candidates plus additional H1 intermarket and volatility-regime candidates have been registered, hash-locked, implemented, smoke-tested, and run through real 9-cell first passes. All were rejected, so diversification remains unsolved. |

Operational prep spec: `docs/PHASE2_OPERATIONS_PREP.md`.

## Current Soak Snapshot

| Field | Value |
| --- | --- |
| Latest status summary | `outputs/reports/PHASE1_STATUS_SUMMARY.json` |
| Latest review bundle | `outputs/review_bundles/PHASE1_DRY_RUN_BUNDLE_20260522_064156.zip` |
| Decision rows | 56 |
| Latest bar | 2026.05.22 20:55:00 |
| Soak progress | 8.26% after v0.6 schema reset |
| Active-market 72-hour streak | Tracked in `PHASE1_STATUS_SUMMARY.json`; still PENDING until longest active-market bar-continuity streak reaches 72h |
| Weekend policy | `weekend_breaks_active_market_streak`; process/code-freeze is tracked separately |
| Process/code-freeze 96-hour gate | Tracked in `PHASE1_STATUS_SUMMARY.json`; still PENDING until process uptime and code-freeze both reach 96h |
| Acceptance | PENDING |

## Decision Rule

```text
IF Phase 1 acceptance = PASS
AND measured cost model = PASS
AND measured-cost revalidation = PASS
AND Phase 1 review index = PASS
AND Phase 2 readiness = PASS
AND active-market 72-hour soak = PASS
AND process/code-freeze 96-hour gate = PASS
AND owner approval file exists
AND owner approval minimum_net_expectancy_r >= 0.15
THEN Phase 2 paper-mode implementation may begin.

ELSE remain in Phase 1 dry-run / Phase 2 preparation.
```

No production-risk behavior is authorized by this checklist.
