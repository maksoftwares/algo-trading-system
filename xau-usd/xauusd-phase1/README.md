# XAUUSD Phase 1

This folder contains the dry-run Master EA shell for the XAUUSD system.

This package is intentionally passive:

- no broker-side execution
- no position management
- no trade modification
- no live expert module yet
- CSV telemetry only

Phase 0 historical validation is closed for the reduced first package, but execution eligibility is now blocked by measured-cost revalidation. `breakout_retest` is cost-suspended, and `swing_breakout_retest_v0` is approved only as a same-family future expert candidate after Gate 9 closure. This phase remains dry-run only: lifecycle, magic-number planning, router/risk contracts, simulated risk caps, spread gating, dashboard state, startup/shutdown logging, and decision logging.

## Scope

| Area | Phase 1 Status |
| --- | --- |
| Dry-run shell | Implemented |
| CSV telemetry | Implemented |
| Lifecycle state | Implemented |
| Risk gate contract | Implemented |
| Router contract | Implemented |
| Expert modules | Dry-run contracts only |
| Live pilot | Out of scope |

## Authorization Boundary

Phase 1 dry-run authorization is now satisfied for telemetry only:

- `breakout_retest` Gate 9 is scored as `PASS`.
- `swing_breakout_retest_v0` Gate 9 is scored as `PASS`, with same-family concentration noted.
- `swing_breakout_retest_v0` is approved as a same-family future expert candidate, not as independent diversification.
- `outputs/reports/PHASE0_VERDICT.md` marks `breakout_retest` as `PASS`.
- `phase0 verify-real-artifacts` returns `PASS`.
- `BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md` currently shows `FAIL`, so no Phase 2 paper-mode implementation is authorized.

The next milestone is clean dry-run infrastructure evidence plus measured-cost audit review, not paper execution.

## Files

- `mt5/Experts/Phase1DryRunShell.mq5`
- `mt5/Config/phase1_dry_run_startup.ini`
- `mt5/Include/Phase1/Phase1Types.mqh`
- `mt5/Include/Phase1/Phase1Logger.mqh`
- `mt5/Include/Phase1/Phase1Risk.mqh`
- `mt5/Include/Phase1/Phase1Router.mqh`
- `mt5/Include/Phase1/Phase1MarketData.mqh`
- `mt5/Include/Phase1/Phase1Session.mqh`
- `mt5/Include/Phase1/Phase1Execution.mqh`
- `mt5/Include/Phase1/Phase1News.mqh`
- `mt5/Include/Phase1/Phase1Dashboard.mqh`
- `mt5/Include/Phase1/Phase1FeatureEngine.mqh`
- `mt5/Include/Phase1/Phase1ServerTime.mqh`
- `mt5/Include/Phase1/Phase1Magic.mqh`
- `mt5/Include/Phase1/Phase1Lifecycle.mqh`
- `mt5/Include/Phase1/Phase1BreakoutRetest.mqh`
- `mt5/Presets/Phase1DryRunShell.safe.set`
- `mt5/Presets/Phase1DryRunShell.test_daily_lock.set`
- `mt5/Presets/Phase1DryRunShell.test_weekly_lock.set`
- `mt5/Presets/Phase1DryRunShell.test_monthly_lock.set`
- `mt5/Presets/Phase1DryRunShell.test_manual_lock.set`
- `docs/PHASE1_DRY_RUN_SCOPE.md`
- `docs/PHASE1_MASTER_EA_DRY_RUN_SPEC.md`
- `docs/CODEX_PHASE1_MASTER_EA_DRY_RUN_PROMPT.md`
- `docs/PHASE2_DRY_RUN_TO_PAPER_PREP_SPEC.md`
- `docs/MAGIC_NUMBERS.md`
- `docs/EXPERT_LIFECYCLE.md`
- `scripts/audit_phase1_safety.py`
- `scripts/deploy_phase1_mt5.py`
- `scripts/verify_phase1_logs.py`
- `scripts/analyze_phase1_soak.py`
- `scripts/generate_phase1_would_signal_report.py`
- `scripts/generate_phase1_runtime_health_report.py`
- `scripts/generate_phase1_acceptance_report.py`
- `scripts/generate_phase1_status_summary.py`
- `scripts/append_phase1_soak_history.py`
- `scripts/generate_phase1_soak_history_report.py`
- `scripts/generate_phase1_review_index.py`
- `scripts/generate_phase2_readiness_report.py`
- `scripts/generate_phase1_bundle.py`

## Expected MT5 Layout

Copy files into MT5 using this shape:

```text
MQL5/
  Experts/
    Phase1DryRunShell.mq5
  Include/
    Phase1/
      Phase1Types.mqh
      Phase1Logger.mqh
      Phase1Risk.mqh
      Phase1Router.mqh
      Phase1MarketData.mqh
      Phase1Session.mqh
      Phase1Execution.mqh
      Phase1News.mqh
      Phase1Dashboard.mqh
      Phase1FeatureEngine.mqh
      Phase1ServerTime.mqh
      Phase1Magic.mqh
      Phase1Lifecycle.mqh
  Presets/
    Phase1DryRunShell.safe.set
```

Attach `Phase1DryRunShell.mq5` to an XAUUSD demo chart. It writes one decision row per new M5 bar when dry-run mode is locked.

## Validation

From this folder:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\audit_phase1_safety.py
..\xauusd-phase0\.venv\Scripts\python.exe -m pytest tests
..\xauusd-phase0\.venv\Scripts\python.exe scripts\deploy_phase1_mt5.py --portable-root C:\MT5PortableGoldMission --compile
..\xauusd-phase0\.venv\Scripts\python.exe scripts\verify_phase1_logs.py --files-dir C:\MT5PortableGoldMission\MQL5\Files
..\xauusd-phase0\.venv\Scripts\python.exe scripts\analyze_phase1_soak.py --files-dir C:\MT5PortableGoldMission\MQL5\Files
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_would_signal_report.py --files-dir C:\MT5PortableGoldMission\MQL5\Files
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_runtime_health_report.py --files-dir C:\MT5PortableGoldMission\MQL5\Files
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_acceptance_report.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log --source-root . --soak-history-report outputs\reports\PHASE1_SOAK_HISTORY_REPORT.md --runtime-health-report outputs\reports\PHASE1_RUNTIME_HEALTH_REPORT.md
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_status_summary.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log --source-root .
..\xauusd-phase0\.venv\Scripts\python.exe scripts\append_phase1_soak_history.py --summary outputs\reports\PHASE1_STATUS_SUMMARY.json --history outputs\reports\PHASE1_SOAK_HISTORY.csv
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_soak_history_report.py --history outputs\reports\PHASE1_SOAK_HISTORY.csv --report outputs\reports\PHASE1_SOAK_HISTORY_REPORT.md
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_review_index.py --root . --report outputs\reports\PHASE1_REVIEW_INDEX.md
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_readiness_report.py --root . --report outputs\reports\PHASE2_READINESS_REPORT.md
..\xauusd-phase0\.venv\Scripts\python.exe scripts\run_phase1_periodic_checks.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files --compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_bundle.py --files-dir C:\MT5PortableGoldMission\MQL5\Files
```

From the repo root, the existing Phase 0 checks should still pass.

`generate_phase1_would_signal_report.py` also writes `outputs/reports/PHASE1_WOULD_SIGNAL_REVIEW.csv` for clustered manual review of dry-run setup observations.
`generate_phase1_runtime_health_report.py` writes `outputs/reports/PHASE1_RUNTIME_HEALTH_REPORT.md` with file, freshness, duplicate-row, and M5 gap checks.
`generate_phase1_status_summary.py` writes `outputs/reports/PHASE1_STATUS_SUMMARY.json` for automation and review dashboards, including runtime-health status.
`append_phase1_soak_history.py` appends each generated status summary to `outputs/reports/PHASE1_SOAK_HISTORY.csv` so the five-day soak has a timestamped progress ledger.
`generate_phase1_soak_history_report.py` writes `outputs/reports/PHASE1_SOAK_HISTORY_REPORT.md` as a reviewer-friendly view of that ledger.
`generate_phase1_review_index.py` writes `outputs/reports/PHASE1_REVIEW_INDEX.md` as the single reviewer entry point.
`generate_phase2_readiness_report.py` writes `outputs/reports/PHASE2_READINESS_REPORT.md` as a preflight gate report for paper-mode preparation.
`run_phase1_periodic_checks.py` can read Phase 1 dry-run logs from one terminal and passive spread logs from a separate logger terminal with `--spread-files-dir`.
