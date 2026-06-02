# Phase 2 Owner Approval + VPS Readiness Package

Last updated: 2026-06-02

Overall status: LOCAL_RUNTIME_SELECTED_OBJECTIVE_GATES_PENDING

This package is a tracked owner handoff for the remaining Phase 2 authorization work. It does not authorize Phase 2 paper mode, demo trading, broker execution, live capital, or any order-placement behavior.

Canonical readiness authority remains:

```text
outputs/reports/PHASE2_READINESS_REPORT.md
```

## Current Decision

| Question | Answer |
| --- | --- |
| Can Phase 2 preparation continue? | YES |
| Can canonical Phase 2 be marked approved now? | NO |
| Can experimental demo evidence continue separately? | YES, but it must not be used to mark canonical readiness PASS |
| Can owner approval be signed now? | NO |
| Selected operating host for next few months | LOCAL_SYSTEM_RUNTIME |
| Main owner action now | Keep formal Phase 2 blocked by confirmed measured-cost failure; continue Phase 0R replacement research |

## Gates Already Closed

| Gate | Status | Evidence |
| --- | --- | --- |
| Phase 1 acceptance | PASS | `outputs/reports/PHASE1_ACCEPTANCE_REPORT.md` |
| Five trading-day soak | PASS | `outputs/reports/PHASE1_SOAK_DRIFT_REPORT.md` |
| Owner-accepted active-market soak | PASS | `docs/PHASE1_ACTIVE_MARKET_SOAK_ACCEPTANCE.md` |
| Code-freeze 96-hour marker | PASS | `outputs/reports/PHASE1_STATUS_SUMMARY.json` |
| Phase 1 observer parity | PASS | `outputs/reports/PHASE1_OBSERVER_PARITY_REPORT.md` |
| Phase 1 review index | PASS | `outputs/reports/PHASE1_REVIEW_INDEX.md` |
| D2 family-clustered validation | PASS | `../xauusd-phase0/outputs/reports/PHASE0_REALITY_CHECK_FAMILY_CLUSTERED.md` |

## Gates Still Blocking Formal Phase 2

| Gate | Current state | Closure condition |
| --- | --- | --- |
| Measured cost model | PASS | `../xauusd-phase0/outputs/reports/MEASURED_COST_MODEL.md` has enough fresh observed market days. |
| Measured-cost revalidation | FAIL | `../xauusd-phase0/outputs/reports/BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` failed with 0/9 passing cells under measured P95 cost. |
| Measured-cost assumption delta | FAIL | `../xauusd-phase0/outputs/reports/MEASURED_COST_ASSUMPTION_DELTA.md` shows measured costs materially exceed configured assumptions. |
| Cost sanity check | CALCULATION_CONFIRMED | `../xauusd-phase0/outputs/reports/MEASURED_COST_REVALIDATION_SANITY_CHECK.md` confirms the measured-cost failure is not currently explained by a conversion bug. |
| Formal Phase 2 | BLOCKED_BY_CONFIRMED_COST_FAILURE | `outputs/reports/PHASE2A_COST_CLOSURE_REPORT.md` and `docs/COST_SUSPENSION_LOCK.md` keep the breakout-retest family execution-blocked. |
| Local runtime first-day verification | PENDING | Generate `outputs/reports/PHASE2_VPS_FIRST_DAY_VERIFICATION.md` after NTP/time sync, backup, recovery, periodic task, MT5 path, compile, startup, decision-log, health, and status evidence are verified for the local system. |
| Project owner approval | PENDING | Create `outputs/reports/PHASE2_OWNER_APPROVAL.md` only after every objective gate above is PASS. |

## Owner VPS Decision Sheet

Owner-selected runtime:

```text
LOCAL_SYSTEM_RUNTIME
```

Accepted period:

```text
Next few months, subject to later owner review.
```

Deferred VPS options:

```text
FXVM Advanced VPS in Dubai/Mumbai/Singapore, ForexVPS.net Core, and QuantVPS Lite remain deferred unless local operation proves inadequate or the owner reopens VPS selection.
```

Required owner decision fields:

| Field | Required value type |
| --- | --- |
| Selected provider | `LOCAL_SYSTEM_RUNTIME` |
| Selected region | Local workstation / operator timezone |
| Selected plan | Existing local Windows workstation |
| Monthly cost | `0 incremental USD/month` |
| Backup method | GitHub/source plus owner-managed local config backup |
| Monitoring endpoint or scheduler | Local Windows Task Scheduler plus dashboard refresh |
| Recovery access owner | Project owner / local machine operator |
| Latency evidence path | `outputs/reports/PHASE2_VPS_LATENCY_REPORT.md` |
| Decision date | `2026-06-02` |
| Owner acceptance | `Phase 2 paper-mode only accepted; no live capital; no broker execution until readiness PASS` |

## VPS Evidence Sequence

1. Keep `LOCAL_SYSTEM_RUNTIME` recorded in `docs/PHASE2_VPS_SELECTION_MATRIX.md`.
2. Keep `outputs/reports/PHASE2_VPS_LATENCY_REPORT.md` generated from the local MT5 baseline.
3. Fill NTP/time-sync, backup, recovery, and periodic scheduler evidence for the local system.
4. Generate the first-day local-runtime verification report.
5. Regenerate Phase 2 readiness and consistency reports.
6. Sign owner approval only if every objective gate is PASS.

## Commands

Refresh the local Phase 2 packets:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\run_phase1_periodic_checks.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files
```

Prepare VPS evidence workspace:

```powershell
.\scripts\prepare_phase2_vps_evidence_workspace.ps1 -Phase1Root .
```

Refresh the local-runtime latency evidence:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_vps_latency_report.py --provider LOCAL_SYSTEM_RUNTIME --region "Local Windows workstation / Asia-Dubai operator timezone" --endpoint "Capital.ComMena MT5 local authorization ping baseline"
```

Validate the VPS selection decision:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_vps_selection_decision_check.py
```

Generate first-day local-runtime verification after evidence is filled:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_vps_first_day_verification.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log --scheduler-evidence outputs\reports\vps_periodic_task.txt
```

## Owner Signing Rule

Do not create:

```text
outputs/reports/PHASE2_OWNER_APPROVAL.md
```

until all objective gates are PASS. The live approval must remain paper-mode only and must include:

- `PHASE2_PAPER_PREP_APPROVED`
- owner name and UTC approval timestamp
- selected VPS provider, region, plan, monthly cost, and latency evidence path
- first-day VPS verification path
- explicit single-edge risk acknowledgement
- explicit no-live-capital acknowledgement
- minimum net expectancy threshold of at least `+0.15R`

Forbidden scope wording in the live owner approval remains:

```text
plus live capital
live trading
broker execution
broker-side execution
order execution
real money
```

## Next Practical Action

The next useful project action is Phase 0R lower-cost replacement research. The next owner-side infrastructure action is still filling and verifying local NTP/time-sync, backup, recovery, and periodic scheduler evidence files, but that will not unblock canonical Phase 2 until measured-cost-aware candidate evidence also passes.
