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
```

## First Run

1. Compile `Phase1DryRunShell.mq5`.
2. Attach it to a demo XAUUSD chart.
3. Keep `InpDryRunOnly=true`.
4. Keep `InpAllowBreakoutRetest=false` until Gate 9 is complete.
5. Inspect `phase1_dry_run_log.csv` from the MT5 files directory.

Expected behavior: one heartbeat row per new M5 bar with lifecycle, spread, router, and blocked-reason fields.
