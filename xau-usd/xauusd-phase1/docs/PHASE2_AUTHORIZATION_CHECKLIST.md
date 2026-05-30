# Phase 2 Authorization Checklist

Last updated: 2026-05-27

This checklist separates work that is already closed from gates that still require wall-clock evidence or explicit owner approval. Phase 2 remains paper-mode preparation only until every required gate below is closed.

## Evidence and Current Gate State

| Item | Status | Evidence |
| --- | --- | --- |
| Phase 0 final verdict | PASS | `breakout_retest` is approved; `swing_breakout_retest_v0` and `symbol_normalized_round_retest_v0` are approved same-family future expert candidates. |
| D1 CPCV | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_CPCV_VALIDATION.md` |
| D2 Reality Check / SPA-style bootstrap | PASS | Active readiness method is owner-accepted `D2_FAMILY_CLUSTERED_V0`: `breakout_retest_family` wins across 67 family representatives, White p=0.0002, and max pairwise SPA p=0.0002; `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REALITY_CHECK_FAMILY_CLUSTERED.md`. Candidate-level D2 remains preserved audit evidence, not the active readiness blocker. It must not be described as candidate-level PASS. |
| D3 true holdout audit | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_TRUE_HOLDOUT_AUDIT.md` |
| D4 independent reproduction | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_INDEPENDENT_REPRODUCTION.md` |
| Same-family second candidate | PASS | `xau-usd/xauusd-phase0/docs/SWING_BREAKOUT_RETEST_V0_GATE9_REVIEW.md` |
| Rejected-candidate gate audit | PASS | Latest audit: 67 audited candidates, 64 rejected/research rows, 14 sample-size failures, 62 multi-cell expectancy failures; `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md` |
| Frequency-normalized concentration audit | PASS | Latest audit: 65 audited candidates, 60 absolute concentration failures, 59 normalized review-context candidates; it does not rescue rejected candidates and is review context only; `xau-usd/xauusd-phase0/outputs/reports/PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md` |
| Diversification availability finding | PASS | Twenty-three non-level H4/D1/W1 candidates plus additional H1 intermarket, volatility-regime, and event-regime candidates were hash-locked and rejected first-pass; current operating frame remains single-edge; `xau-usd/xauusd-phase0/docs/DIVERSIFICATION_AVAILABILITY_FINDING.md` |
| Forward hypothesis gates | PASS | `docs/HYPOTHESIS_LOCKING.md` pre-registers normalized concentration thresholds and a Pepperstone+Dukascopy cross-venue PF floor for future candidates. |
| Phase 1 dry-run compile | PASS | `C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log` |
| Phase 1 source safety | PASS | `scripts/audit_phase1_safety.py` |
| Phase 1 runtime health | WARN | `outputs/reports/PHASE1_RUNTIME_HEALTH_REPORT.md`; remaining warnings are maturity gates after the v0.7 reset. `docs/PHASE1_GAP_CLASSIFICATION_REVIEW.md` is superseded by the shared gap classifier: configured expected broker maintenance gaps pause the active-market streak without counting elapsed closed-market time; unexpected gaps, restarts, and unsafe states still reset it. |
| Phase 1 would-signal evidence | PASS | `outputs/reports/PHASE1_WOULD_SIGNAL_REPORT.md` |
| Fixed-notional cost report | PASS | `xau-usd/xauusd-phase0/outputs/reports/FIXED_NOTIONAL_REPORT.md` |
| Passive spread logger deployment | PASS | Deployed, compiled, and producing logs in the isolated logger clone; `xau-usd/xauusd-phase0/outputs/reports/PASSIVE_SPREAD_LOGGER_DEPLOYMENT.md` |
| Phase 2 cost-measurement protocol | PASS | `docs/PHASE2_COST_MEASUREMENT_PROTOCOL.md` documents Phase 2 as a cost-measurement experiment and pre-commits the +0.15R suspension rule. |
| Single-edge risk plan | PASS | `docs/PHASE2_SINGLE_EDGE_RISK_PLAN.md` treats same-family variants as one correlated breakout-retest family and marks the family as cost-revalidation-pending until fresh measured-cost revalidation passes. |
| Local MT5 broker-access baseline | PASS | `outputs/reports/PHASE2_LOCAL_MT5_NETWORK_BASELINE.md` provides the sanitized local MT5 authorization-ping benchmark that selected VPS latency must be compared against. |
| External health monitor | PASS | `docs/PHASE2_OPERATIONS_PREP.md` defines the out-of-terminal monitor and local scheduler-friendly check script. |
| Disaster recovery runbook | PASS | `docs/PHASE2_OPERATIONS_PREP.md` documents recovery assets, procedure, and rollback rule. |
| Capital allocation ladder | PASS | `docs/PHASE2_SINGLE_EDGE_RISK_PLAN.md` defines the paper-to-micro ladder and single-edge sizing constraint. |
| Quarterly/review triggers | PASS | `docs/PHASE2_SINGLE_EDGE_RISK_PLAN.md` defines cost, trade-count, PF, drawdown, concentration, execution, and logic triggers. |
| Five trading day soak | PASS | `PHASE1_ACCEPTANCE_REPORT.md` shows the five-day wall-clock soak has crossed 100%. |
| VPS shortlist | READY_FOR_OWNER_SELECTION | `docs/PHASE2_VPS_SELECTION_MATRIX.md` now contains a shortlist, latency-test rule, and first-day verification packet. |
| Owner approval draft | READY_FOR_OWNER_SELECTION | `docs/PHASE2_OWNER_APPROVAL_DRAFT.md` is prepared as a non-authorizing draft. Do not create the live approval file until all objective gates pass and the owner signs. |

## Still Pending

| Gate | Current status | Closure rule |
| --- | --- | --- |
| Active-market 72-hour soak | PENDING | `PHASE1_ACCEPTANCE_REPORT.md` and `PHASE1_STATUS_SUMMARY.json` must show longest active-market bar-continuity streak >= 72h with no dry-run, permission, schema, server-time, run-reset, or unexpected-gap violations. Expected broker maintenance gaps pause the streak without adding closed-market time. |
| Process/code-freeze 96-hour gate | PENDING | `PHASE1_ACCEPTANCE_REPORT.md` and `PHASE1_STATUS_SUMMARY.json` must show process uptime streak >= 96h and code-freeze hours >= 96h using `phase1_code_freeze_started_at.txt`. |
| Measured cost model | PENDING | `xau-usd/xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md` must show PASS from five fresh observed market days before evaluation. |
| Measured-cost revalidation | PENDING | `xau-usd/xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` must be rerun after measured cost model PASS and show PASS before any paper-mode implementation. |
| Measured-cost assumption delta | PENDING | `xau-usd/xauusd-phase0/outputs/reports/MEASURED_COST_ASSUMPTION_DELTA.md` remains pending until authoritative measured-cost revalidation runs. |
| Measured-cost audit | REVIEW | `xau-usd/xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_AUDIT.md` and `BREAKOUT_RETEST_COST_R_DIAGNOSTIC.md` must be reviewed to decide whether the cost failure is real or a conversion defect. |
| Phase 1 review index | PENDING | `PHASE1_REVIEW_INDEX.md` must show PASS after acceptance and bundle refresh. |
| Phase 2 readiness report | PENDING | `PHASE2_READINESS_REPORT.md` must return to PASS after all remaining readiness gates are closed. D2 is no longer the active blocker after owner acceptance of `D2_FAMILY_CLUSTERED_V0`. |
| Phase 1 observer parity | PENDING | `PHASE1_OBSERVER_PARITY_REPORT.md` must prove the MQL Phase 1 observer remains aligned with the Python Phase 0 `breakout_retest` logic before paper-mode implementation. |
| Project owner approval | PENDING | Use `docs/PHASE2_OWNER_APPROVAL_DRAFT.md` after all objective gates pass, then add `outputs/reports/PHASE2_OWNER_APPROVAL.md` only when the owner explicitly authorizes paper-mode work. |
| VPS selection | PENDING | Shortlist is ready. `docs/PHASE2_VPS_SELECTION_MATRIX.md` must show `Overall status: PASS` only after provider, region, specs, backup access, monitoring approach, and first-day latency evidence are selected. |
| VPS latency evidence | PENDING | Run `scripts/generate_phase2_vps_latency_report.py` on the selected VPS and require `outputs/reports/PHASE2_VPS_LATENCY_REPORT.md` to show PASS before VPS selection can close. The selected VPS must also be compared against `outputs/reports/PHASE2_LOCAL_MT5_NETWORK_BASELINE.md`; if it does not materially improve on local median ping, owner review is required before treating it as an operational improvement. |
| VPS first-day verification | PENDING | Require `outputs/reports/PHASE2_VPS_FIRST_DAY_VERIFICATION.md` to show PASS after selected-VPS consistency, NTP/time sync, backup, recovery login, periodic scheduler, MT5 path, compile, startup, decision-log, external-health, and status-summary evidence are captured. The selected provider/region in the decision record, latency report, and manual VPS evidence must match. |
| Non-level/intermarket forcing candidate run | PASS | Twenty-three non-level H4/D1/W1 candidates plus additional H1 intermarket, volatility-regime, and event-regime candidates have been registered, hash-locked, implemented, smoke-tested, and run through real 9-cell first passes. All were rejected, so diversification remains unsolved. |

Operational prep spec: `docs/PHASE2_OPERATIONS_PREP.md`.

## Current State Source

| Field | Value |
| --- | --- |
| Canonical current state | `outputs/reports/PHASE1_STATUS_SUMMARY.json` |
| Latest review bundle | Read from the latest bundle manifest in `outputs/review_bundles/` |
| Decision rows | Do not pin in static docs; read `runtime.decision_rows` from `PHASE1_STATUS_SUMMARY.json` |
| Latest bar | Do not pin in static docs; read `runtime.latest_row.bar_time` from `PHASE1_STATUS_SUMMARY.json` |
| Soak progress | Do not pin in static docs; read `soak.progress_pct` from `PHASE1_STATUS_SUMMARY.json` |
| Active-market 72-hour streak | Tracked in `PHASE1_STATUS_SUMMARY.json`; still PENDING until longest active-market bar-continuity streak reaches 72h |
| Expected market-break policy | `expected_market_breaks_pause_active_market_streak`; process/code-freeze is tracked separately |
| Process/code-freeze 96-hour gate | Tracked in `PHASE1_STATUS_SUMMARY.json`; still PENDING until process uptime and code-freeze both reach 96h |
| Acceptance | Read `status.acceptance` from `PHASE1_STATUS_SUMMARY.json` |

## Decision Rule

```text
IF Phase 1 acceptance = PASS
AND measured cost model = PASS
AND measured-cost revalidation = PASS after any required cost-conversion correction
AND Phase 1 review index = PASS
AND Phase 1 observer parity = PASS
AND Phase 2 readiness = PASS
AND VPS latency evidence = PASS
AND selected VPS latency is compared against PHASE2_LOCAL_MT5_NETWORK_BASELINE.md
AND selected VPS decision record matches latency and first-day manual evidence
AND VPS first-day verification = PASS
AND active-market 72-hour soak = PASS
AND process/code-freeze 96-hour gate = PASS
AND owner approval file exists
AND owner approval minimum_net_expectancy_r >= 0.15
THEN Phase 2 paper-mode implementation may begin.

ELSE remain in Phase 1 dry-run / Phase 2 preparation.
```

No production-risk behavior is authorized by this checklist.
