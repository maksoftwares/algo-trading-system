# Phase 1 MT5 Files

This folder contains the Phase 1 dry-run shell for MT5.

The shell writes CSV telemetry only. It is not an approved expert implementation and it cannot be used for broker-side execution.

## Install Layout

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
      Phase1BreakoutRetest.mqh
```

## First Run

1. Compile `Phase1DryRunShell.mq5`.
2. Attach it to a demo XAUUSD chart.
3. Keep `InpDryRunOnly=true`.
4. Keep `InpObserveBreakoutRetest=true` only for dry-run observation.
5. Inspect `decision_log.csv`, `startup_log.csv`, and `shutdown_log.csv` from the MT5 files directory.

Expected behavior: one decision row per new M5 bar with session, regime, simulated risk caps, execution, news, lifecycle, server-time, feature, breakout-retest observer, router, and blocked-reason fields.

## Deploy And Compile

From the Phase 1 folder:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\deploy_phase1_mt5.py --portable-root C:\MT5PortableGoldMission --compile
```

To mirror into the mapped terminal data MQL5 root as well:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\deploy_phase1_mt5.py --portable-root C:\MT5PortableGoldMission --data-mql5-root "C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\FDAC074599BBCDE0F5549DAB937D2E01\MQL5" --compile
```

## Restart Verification

After restarts, run:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\verify_phase1_logs.py --files-dir C:\MT5PortableGoldMission\MQL5\Files
```

The verifier fails on duplicate CSV headers, missing required columns, or any decision row that grants permission. Restart rows for the same M5 bar are tolerated when they belong to different run IDs.

## Soak Analysis

Generate the soak/drift report from the Phase 1 folder:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\analyze_phase1_soak.py --files-dir C:\MT5PortableGoldMission\MQL5\Files
```

The report summarizes dry-run state, permission state, lifecycle rows, per-run M5 cadence, latest-row freshness, server-time status, spread points, stale seconds, and breakout-retest observer states.

## Acceptance Report

Generate the acceptance report from the Phase 1 folder:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_acceptance_report.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log --source-root . --soak-history-report outputs\reports\PHASE1_SOAK_HISTORY_REPORT.md --runtime-health-report outputs\reports\PHASE1_RUNTIME_HEALTH_REPORT.md
```

The report combines compile status, source safety audit, runtime log verification, soak/drift status, runtime health, would-signal evidence, soak-history status, dry-run state, permission state, runtime freshness, latest runtime row, and the five-trading-day soak gate. The expected current state is `PENDING` until enough wall-clock soak data exists.

## Runtime Health

Generate the runtime health and gap report:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_runtime_health_report.py --files-dir C:\MT5PortableGoldMission\MQL5\Files
```

The report checks runtime file presence, latest-row freshness, dry-run state, permission state, server-time status, exact duplicates, unique M5 gaps, and lifecycle row balance.

## Would-Signal Evidence

Generate the dry-run would-signal report from the Phase 1 folder:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_would_signal_report.py --files-dir C:\MT5PortableGoldMission\MQL5\Files
```

The report extracts every breakout-retest `WOULD_SIGNAL` row, groups rows into setup clusters, writes `PHASE1_WOULD_SIGNAL_REVIEW.csv`, and verifies those rows stayed dry-run and permission-locked.

## Review Bundle

Generate a review bundle from the Phase 1 folder:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_bundle.py --files-dir C:\MT5PortableGoldMission\MQL5\Files
```

The bundle includes source, docs, presets, tests, the log report, the soak/drift report, the would-signal report plus review CSV, the acceptance report, MT5 runtime CSVs, the compile log when present, and a SHA256 manifest.

## Review Index

Generate the reviewer entry-point index:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_review_index.py --root . --report outputs\reports\PHASE1_REVIEW_INDEX.md
```

The index summarizes acceptance, runtime health, dry-run logs, soak/drift, would-signal evidence, soak history, the status summary JSON, and the latest review bundle path.

## Phase 2 Readiness

Generate the Phase 2 readiness/preflight report:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_readiness_report.py --root . --report outputs\reports\PHASE2_READINESS_REPORT.md
```

The report is expected to remain `PENDING` until Phase 1 acceptance, the review index, the five-trading-day soak gate, and project-owner approval all pass.

## Status Summary

Generate the machine-readable status summary from the Phase 1 folder:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_status_summary.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log --source-root .
```

The summary writes `PHASE1_STATUS_SUMMARY.json` with verification status, runtime-health status, acceptance status, latest runtime row, would-signal counts, setup cluster counts, and five-trading-day soak progress.

## Soak History

Append the latest status summary to the soak history ledger:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\append_phase1_soak_history.py --summary outputs\reports\PHASE1_STATUS_SUMMARY.json --history outputs\reports\PHASE1_SOAK_HISTORY.csv
```

The history CSV keeps one row per generated summary timestamp, including verification status, acceptance status, latest M5 bar, would-signal counts, and five-trading-day soak progress.

Generate the reviewer-facing history report:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase1_soak_history_report.py --history outputs\reports\PHASE1_SOAK_HISTORY.csv --report outputs\reports\PHASE1_SOAK_HISTORY_REPORT.md
```

## Risk Simulation Presets

These presets are dry-run diagnostics:

```text
Phase1DryRunShell.test_daily_lock.set
Phase1DryRunShell.test_weekly_lock.set
Phase1DryRunShell.test_monthly_lock.set
Phase1DryRunShell.test_manual_lock.set
```

Each one keeps `InpDryRunOnly=true` and changes only the simulated risk inputs.
