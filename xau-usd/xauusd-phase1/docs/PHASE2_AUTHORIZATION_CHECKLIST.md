# Phase 2 Authorization Checklist

Last updated: 2026-06-01

This checklist separates work that is already closed from gates that still require wall-clock evidence or explicit owner approval. Phase 2 remains paper-mode preparation only until every required gate below is closed.

Authority rule: `outputs/reports/PHASE2_READINESS_REPORT.md` is the sole current readiness authority. This checklist records policy requirements and evidence pointers; if a generated report disagrees with this static checklist, regenerate reports and use `PHASE2_READINESS_REPORT.md` for the go/no-go decision.

## Evidence and Current Gate State

| Item | Status | Evidence |
| --- | --- | --- |
| Phase 0 final verdict | PASS | `breakout_retest` is approved; `swing_breakout_retest_v0` and `symbol_normalized_round_retest_v0` are approved same-family future expert candidates. |
| D1 CPCV | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_CPCV_VALIDATION.md` |
| D2 Reality Check / SPA-style bootstrap | PASS | Active readiness method is owner-accepted `D2_FAMILY_CLUSTERED_V0`: `breakout_retest_family` wins across 67 family representatives, White p=0.0002, and max pairwise SPA p=0.0002; `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REALITY_CHECK_FAMILY_CLUSTERED.md`. Candidate-level D2 remains preserved audit evidence, not the active readiness blocker. It must not be described as candidate-level PASS. |
| D3 true holdout audit | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_TRUE_HOLDOUT_AUDIT.md` |
| D4 independent reproduction | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_INDEPENDENT_REPRODUCTION.md` |
| Same-family second candidate | PASS | `xau-usd/xauusd-phase0/docs/SWING_BREAKOUT_RETEST_V0_GATE9_REVIEW.md` |
| Rejected-candidate gate audit | PASS | Latest audit: 143 audited candidates, 140 rejected/research rows, 32 sample-size failures, 136 multi-cell expectancy failures; `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md` |
| Frequency-normalized concentration audit | PASS | Latest audit: 117 result-producing candidates, 111 absolute concentration failures, and 110 normalized review-context candidates; it does not rescue rejected candidates and is review context only; `xau-usd/xauusd-phase0/outputs/reports/PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md` |
| Diversification availability finding | PASS | Twenty-nine H4/D1/W1 candidates plus additional H1 intermarket, volatility-regime, event-regime, macro, ETF, FX, futures-proxy, volatility-premium, and calendar/microstructure candidates were hash-locked and rejected first-pass; current operating frame remains single-edge; `xau-usd/xauusd-phase0/docs/DIVERSIFICATION_AVAILABILITY_FINDING.md` |
| Forward hypothesis gates | PASS | `docs/HYPOTHESIS_LOCKING.md` pre-registers normalized concentration thresholds and a Pepperstone+Dukascopy cross-venue PF floor for future candidates. |
| Phase 1 dry-run compile | PASS | `C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log` |
| Phase 1 source safety | PASS | `scripts/audit_phase1_safety.py` |
| Phase 1 runtime health | PASS | `outputs/reports/PHASE1_RUNTIME_HEALTH_REPORT.md`; runtime boundary is clean. `docs/PHASE1_GAP_CLASSIFICATION_REVIEW.md` is superseded by the shared gap classifier for calculations, but remains retained as audit context. The current expected broker maintenance gaps pause policy remains documented as historical soak context. |
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
| Phase 1 active-market soak | PASS | Active-market soak: PASS via owner-accepted 56h threshold; original 72h target waived for Phase 1 dry-run closure only. Evidence: `docs/PHASE1_ACTIVE_MARKET_SOAK_ACCEPTANCE.md`, `outputs/reports/PHASE1_ACCEPTANCE_REPORT.md`, and `outputs/reports/PHASE1_STATUS_SUMMARY.json`. |
| Code-freeze marker gate | PASS | Current gate is code-freeze marker age only; process uptime after restart is informational. Phase 2 still needs fresh VPS-specific process/first-day verification if relevant. Evidence: `outputs/reports/PHASE1_STATUS_SUMMARY.json`. |
| Phase 1 observer parity | PASS | `PHASE1_OBSERVER_PARITY_REPORT.md` proves the MQL Phase 1 observer remains aligned with the Python Phase 0 `breakout_retest` logic. |
| Phase 1 review index | PASS | `PHASE1_REVIEW_INDEX.md` is PASS after Phase 1 closure and bundle refresh. |
| Runtime host selection | PASS | Owner selected `LOCAL_SYSTEM_RUNTIME` for the next few months in `docs/PHASE2_VPS_SELECTION_MATRIX.md`; no VPS latency-improvement claim is made. |
| Runtime latency evidence | PASS | `outputs/reports/PHASE2_VPS_LATENCY_REPORT.md` uses the local MT5 baseline for `LOCAL_SYSTEM_RUNTIME`. |
| Owner approval draft | READY_FOR_OWNER_SELECTION | `docs/PHASE2_OWNER_APPROVAL_DRAFT.md` is prepared as a non-authorizing draft. Do not create the live approval file until all objective gates pass and the owner signs. |
| Owner/VPS readiness package | READY_FOR_OWNER_SELECTION | `docs/PHASE2_OWNER_VPS_READINESS_PACKAGE.md` summarizes the remaining owner decisions, VPS evidence sequence, generated packet paths, and paper-only signing rule. |

## Still Pending

| Gate | Current status | Closure rule |
| --- | --- | --- |
| Measured cost model | PENDING | `xau-usd/xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md` must show PASS from five fresh observed market days before evaluation. |
| Measured-cost revalidation | PENDING | `xau-usd/xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` must be rerun after measured cost model PASS and show PASS before any paper-mode implementation. |
| Measured-cost assumption delta | PENDING | `xau-usd/xauusd-phase0/outputs/reports/MEASURED_COST_ASSUMPTION_DELTA.md` remains pending until authoritative measured-cost revalidation runs. |
| Measured-cost audit | REVIEW | `xau-usd/xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_AUDIT.md` and `BREAKOUT_RETEST_COST_R_DIAGNOSTIC.md` must be reviewed to decide whether the cost failure is real or a conversion defect. |
| Phase 2 readiness report | PENDING | `PHASE2_READINESS_REPORT.md` must return to PASS after all remaining readiness gates are closed. D2 is no longer the active blocker after owner acceptance of `D2_FAMILY_CLUSTERED_V0`. |
| Demo account isolation/preflight | FAIL/PENDING | `PHASE2_DEMO_ACCOUNT_ISOLATION_REPORT.md` records the clean owner-opened demo terminal evidence, but `PHASE2_DEMO_PREFLIGHT_REPORT.md` may remain FAIL/PENDING until clean demo/VPS-specific Phase 2 evidence replaces local live-server markers and all readiness gates pass. |
| Project owner approval | PENDING | Use `docs/PHASE2_OWNER_APPROVAL_DRAFT.md` after all objective gates pass, then add `outputs/reports/PHASE2_OWNER_APPROVAL.md` only when the owner explicitly authorizes paper-mode work. |
| Local runtime first-day verification | PENDING | Require `outputs/reports/PHASE2_VPS_FIRST_DAY_VERIFICATION.md` to show PASS after local-runtime consistency, NTP/time sync, backup, recovery login, periodic scheduler, MT5 path, compile, startup, decision-log, external-health, and status-summary evidence are captured. The selected provider/region in the decision record, latency report, and manual runtime evidence must match. |
| Non-level/intermarket forcing candidate run | PASS | Twenty-nine H4/D1/W1 candidates plus additional H1 intermarket, volatility-regime, event-regime, macro, ETF, FX, futures-proxy, volatility-premium, and calendar/microstructure candidates have been registered, hash-locked, implemented, smoke-tested, and run through real 9-cell first passes. All independent candidates were rejected, so diversification remains unsolved. |

Operational prep spec: `docs/PHASE2_OPERATIONS_PREP.md`.

## Current State Source

| Field | Value |
| --- | --- |
| Canonical current state | `outputs/reports/PHASE1_STATUS_SUMMARY.json` |
| Latest review bundle | Read from the latest bundle manifest in `outputs/review_bundles/` |
| Decision rows | Do not pin in static docs; read `runtime.decision_rows` from `PHASE1_STATUS_SUMMARY.json` |
| Latest bar | Do not pin in static docs; read `runtime.latest_row.bar_time` from `PHASE1_STATUS_SUMMARY.json` |
| Soak progress | Do not pin in static docs; read `soak.progress_pct` from `PHASE1_STATUS_SUMMARY.json` |
| Active-market soak | PASS via owner-accepted 56h threshold in `PHASE1_STATUS_SUMMARY.json`; original 72h target is waived for Phase 1 dry-run closure only |
| Expected market-break policy | `expected_market_breaks_pause_active_market_streak`; process/code-freeze is tracked separately |
| Code-freeze marker gate | PASS in `PHASE1_STATUS_SUMMARY.json`; current process uptime after restart is informational, not a reset of the marker-age gate |
| Acceptance | Read `status.acceptance` from `PHASE1_STATUS_SUMMARY.json` |

## Decision Rule

```text
IF Phase 1 acceptance = PASS
AND Phase 1 active-market soak = PASS via owner-accepted 56h threshold
AND code-freeze marker gate = PASS
AND measured cost model = PASS
AND measured-cost revalidation = PASS after any required cost-conversion correction
AND Phase 1 review index = PASS
AND Phase 1 observer parity = PASS
AND Phase 2 readiness = PASS
AND runtime latency evidence = PASS
AND selected runtime decision record matches latency and first-day manual evidence
AND local runtime first-day verification = PASS
AND owner approval file exists
AND owner approval minimum_net_expectancy_r >= 0.15
THEN Phase 2 paper-mode implementation may begin.

ELSE remain in Phase 1 dry-run / Phase 2 preparation.
```

No production-risk behavior is authorized by this checklist.
