# Phase 2 Operations Prep

Last updated: 2026-05-22

This document prepares the operational pieces needed before paper-mode work is authorized. It does not authorize production-risk behavior. The Phase 1 dry-run shell remains permission-locked until the Phase 1 acceptance and owner approval gates pass.

## VPS Selection Plan

Minimum target:

| Area | Requirement |
| --- | --- |
| Region | Same region or nearest practical region to the broker trade server. |
| Uptime | Provider with published high-availability history and restart controls. |
| CPU / RAM | At least 2 vCPU and 4 GB RAM for one terminal plus monitoring tools. |
| Storage | SSD, at least 60 GB, with enough free space for logs and weekly bundles. |
| Access | Administrator access, documented recovery login, and password/key rotation. |
| Time | NTP enabled; server timezone documented; broker, UTC, and local timestamps preserved in logs. |
| Backups | Weekly image or file backup, plus repo and config backup after every release slice. |

Decision record to fill before Phase 2:

| Field | Value |
| --- | --- |
| Provider | Pending owner selection |
| Region | Pending owner selection |
| Monthly cost | Pending owner selection |
| Backup method | Pending owner selection |
| Monitoring endpoint | Pending external monitor setup |

## External Health Monitor Spec

Goal:

Detect stalled telemetry from outside the terminal environment. The first monitor can be simple: a separate host or cloud job checks that the latest status summary, decision log, and runtime files are fresh.

Minimum checks:

| Check | Rule |
| --- | --- |
| Decision log freshness | Latest row age must stay below the configured freshness limit during market hours. |
| Dry-run boundary | Latest status summary must keep `dry_run=true` and `trade_permission=false` during Phase 1. |
| Server-time state | Latest row must show `server_time_status=CLOCK_OK` or the monitor should alert. |
| Bundle cadence | A review bundle or status summary should be refreshed on schedule. |
| Disk space | Free space must stay above a fixed floor. |
| Process presence | Terminal and monitor process must be running during planned soak windows. |

Alert routing:

| Severity | Example | Action |
| --- | --- | --- |
| Warning | One stale summary or a missed hourly bundle | Notify owner and keep observing. |
| Critical | No fresh rows for more than one market hour | Notify owner and pause phase advancement. |
| Stop-review | Safety boundary violation | Stop acceptance review until root cause is documented. |

Implementation note:

The existing local scripts already produce the data the monitor needs. Phase 2 should add the separate-host scheduler, not another in-terminal-only check.

Prepared local check:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\check_phase1_external_health.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --status-summary outputs\reports\PHASE1_STATUS_SUMMARY.json
```

This script is intentionally scheduler-friendly: it exits nonzero on health failure and can write `outputs/reports/PHASE1_EXTERNAL_HEALTH.json`.

Prepared periodic command:

```powershell
..\xauusd-phase0\.venv\Scripts\python.exe scripts\run_phase1_periodic_checks.py --files-dir C:\MT5PortableGoldMission\MQL5\Files --spread-files-dir C:\MT5PortableSpreadLogger\MQL5\Files --compile-log C:\MT5PortableGoldMission\compile_Phase1DryRunShell.log
```

This wraps status summary, soak history, acceptance, review index, Phase 2 readiness, and external health into one scheduler entry point.
Use `--spread-files-dir` when the passive spread logger is isolated in a second MT5 Portable instance so Phase 1 soak telemetry and spread-cost telemetry do not compete for the same chart.

## Disaster Recovery Runbook

Recovery target:

Return to a known dry-run or paper-mode state from GitHub plus the latest saved MT5 files, without relying on memory.

Required recovery assets:

| Asset | Location |
| --- | --- |
| Source repository | GitHub `main` branch |
| Phase 1/2 docs | `xau-usd/xauusd-phase1/docs` |
| MT5 source files | `xau-usd/xauusd-phase1/mt5` |
| Runtime evidence | `xau-usd/xauusd-phase1/outputs` and saved terminal `MQL5/Files` logs |
| Compile log | Portable terminal compile log |
| Owner approval artifacts | `outputs/reports` |

Recovery procedure:

1. Clone or update the repository on the recovery machine.
2. Install the Python runtime and Phase 0 package used by Phase 1 scripts.
3. Deploy the Phase 1/2 MT5 files using the deployment helper.
4. Compile the shell and save the compile log.
5. Start the terminal in the approved mode for the current phase.
6. Run log verification, runtime health, soak analysis, and safety audit.
7. Generate a fresh status summary and review bundle.
8. Compare latest runtime row against the last known accepted state.
9. Document the incident, recovery time, and any missing logs.

Rollback rule:

If verification fails after recovery, return to the last committed version that had passing safety, tests, compile evidence, and runtime health. Do not advance phases during a recovery incident.

## Capital Allocation Ladder

Paper-mode first:

Phase 2 should use paper-mode only. Any later funding decision must be based on paper evidence, not Phase 0 backtests alone.

Draft ladder:

| Stage | Condition | Risk posture |
| --- | --- | --- |
| Phase 2 paper | Phase 1 acceptance PASS and owner approval | Simulated or paper-only, no capital exposure. |
| Micro pilot | Paper evidence reviewed and drift acceptable | Lowest practical size, below the original v0.3 plan because only one expert is approved. |
| Step 1 | Stable trade count, drawdown, and behavior review | Small fixed risk, no compounding. |
| Step 2 | Additional review period passes | Modest increase only if concentration and drift remain acceptable. |
| Stop | Drift, logic gap, or drawdown trigger fires | Freeze step-up and return to review. |

Single-expert adjustment:

Because only `breakout_retest` is approved, any live-capital stage should start lower than the earlier diversified-portfolio assumption. The second candidate research track must continue in parallel.

## Review Triggers

Quarterly review should not be calendar-only. Trigger review immediately if any of these occur:

| Trigger | Rule |
| --- | --- |
| Trade count drift | Observed paper/live trade count deviates materially from Phase 0 expectation. |
| PF drift | Rolling PF falls below the pre-defined warning threshold. |
| Drawdown | Daily, weekly, monthly, or rolling drawdown reaches warning state. |
| Concentration | A small number of trades explain too much of observed PnL. |
| Execution quality | Spread, slippage proxy, stale tick, or broker-state warnings rise. |
| Logic mismatch | Dry-run or paper observations show the expert behaving outside the hypothesis. |
| Data issue | Missing bars, duplicate rows, timestamp drift, or terminal restarts affect evidence quality. |

Required review output:

```text
PHASE_REVIEW_<YYYY_QN>.md
```

The review must state one of:

```text
CONTINUE
CONTINUE_WITH_REDUCED_RISK
SUSPEND
RETIRE
RESEARCH_REPLACEMENT
```

No review may rewrite the original hypothesis to fit observed results. New ideas must become new versioned hypotheses.
