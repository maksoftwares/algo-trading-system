# Phase 2 Authorization Checklist

Last updated: 2026-05-22

This checklist separates work that is already closed from gates that still require wall-clock evidence or explicit owner approval. Phase 2 remains paper-mode preparation only until every required gate below is closed.

## Closed Evidence

| Item | Status | Evidence |
| --- | --- | --- |
| Phase 0 final verdict | PASS | `breakout_retest` is approved; `swing_breakout_retest_v0` is approved as a same-family future expert candidate. |
| D1 CPCV | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_CPCV_VALIDATION.md` |
| D2 Reality Check / SPA-style bootstrap | PASS | Review #3 rerun against 18 non-empty matrix-ledger candidates: White p=0.0200, max SPA p=0.0336; `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REALITY_CHECK.md` |
| D3 true holdout audit | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_TRUE_HOLDOUT_AUDIT.md` |
| D4 independent reproduction | PASS | `xau-usd/xauusd-phase0/outputs/reports/PHASE0_INDEPENDENT_REPRODUCTION.md` |
| Same-family second candidate | PASS | `xau-usd/xauusd-phase0/docs/SWING_BREAKOUT_RETEST_V0_GATE9_REVIEW.md` |
| Rejected-candidate gate audit | PASS | Review #3 V3: 17 rejected/research candidates audited, 4 sample-size failures, 17 multi-cell expectancy failures, 0 frequency-only failures; `xau-usd/xauusd-phase0/outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md` |
| Phase 1 dry-run compile | PASS | `C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log` |
| Phase 1 source safety | PASS | `scripts/audit_phase1_safety.py` |
| Phase 1 runtime health | PASS | `outputs/reports/PHASE1_RUNTIME_HEALTH_REPORT.md` |
| Phase 1 would-signal evidence | PASS | `outputs/reports/PHASE1_WOULD_SIGNAL_REPORT.md` |
| Fixed-notional cost report | PASS | `xau-usd/xauusd-phase0/outputs/reports/FIXED_NOTIONAL_REPORT.md` |
| Passive spread logger deployment | PASS | Deployed, compiled, and producing logs in the isolated logger clone; `xau-usd/xauusd-phase0/outputs/reports/PASSIVE_SPREAD_LOGGER_DEPLOYMENT.md` |

## Still Pending

| Gate | Current status | Closure rule |
| --- | --- | --- |
| Five trading day soak | PENDING | `PHASE1_ACCEPTANCE_REPORT.md` must show five-day soak PASS. |
| Measured cost model | PENDING | `xau-usd/xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md` must show PASS. |
| Measured-cost revalidation | PENDING | `xau-usd/xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` must show PASS. |
| Phase 1 review index | PENDING | `PHASE1_REVIEW_INDEX.md` must show PASS after acceptance and bundle refresh. |
| Phase 2 readiness report | PENDING | `PHASE2_READINESS_REPORT.md` must show PASS. |
| Project owner approval | PENDING | Add `outputs/reports/PHASE2_OWNER_APPROVAL.md` after the owner explicitly authorizes paper-mode work. |
| VPS selection | PENDING | Document provider, region, specs, backup access, and monitoring approach. |
| External health monitor | PENDING | Define an out-of-terminal heartbeat or file freshness monitor. |
| Disaster recovery runbook | PENDING | Document restore, redeploy, log recovery, and rollback procedure. |
| Capital allocation ladder | PENDING | Define paper-mode sizing, step-up rules, and stop conditions. |
| Measured-cost suspension rule | PENDING | Before Phase 2, document the pre-committed rule: suspend the breakout-retest family if measured paper/live execution cost pushes net expectancy below +0.10R. |
| Quarterly review triggers | PENDING | Document drift, drawdown, trade-count, and behavior-review triggers. |
| Independent second candidate implementation | PENDING | Keep searching for a non-breakout-retest-family candidate; same-family swing candidate is not independent diversification. |

Operational prep spec: `docs/PHASE2_OPERATIONS_PREP.md`.

## Current Soak Snapshot

| Field | Value |
| --- | --- |
| Latest status summary | `outputs/reports/PHASE1_STATUS_SUMMARY.json` |
| Latest review bundle | `outputs/review_bundles/PHASE1_DRY_RUN_BUNDLE_20260522_064156.zip` |
| Decision rows | 27 |
| Latest bar | 2026.05.22 12:40:00 |
| Soak progress | 1.39% after v0.6 schema reset |
| Acceptance | PENDING |

## Decision Rule

```text
IF Phase 1 acceptance = PASS
AND measured cost model = PASS
AND measured-cost revalidation = PASS
AND Phase 1 review index = PASS
AND Phase 2 readiness = PASS
AND owner approval file exists
THEN Phase 2 paper-mode implementation may begin.

ELSE remain in Phase 1 dry-run / Phase 2 preparation.
```

No production-risk behavior is authorized by this checklist.
