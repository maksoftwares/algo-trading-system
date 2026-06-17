# CODEX WORK ORDER — Live health check at market open (2026-06-14, Sunday-evening open)

Owner: Ali (mohdalikhans97.com@gmail.com), 2026-06-14. Demo only.

## Why now
The market just reopened (~22:00 UTC) and the hourly supervisor's 22:03Z snapshot is **RED**:
it reports `RUNTIME_LOGS_MISSING_GT_90_MIN` (it cannot read runtime signal/order logs),
it is only watching the old P2WEAKNESS/canonical lane (not A2/A3/the publisher), and it flags
the P2WEAKNESS lane as armed (`broker_action=true`) with its **kill-switch file missing** and
old magic `930101` active. We need a real, live read of the whole rig.

## Boundaries
- **Read-only verification + diagnosis.** Do NOT change trade logic, session gates, magics,
  presets, or arming flags — **except one safety-restoring exception:** if a lane is found
  armed (`broker_action=true`) without its kill-switch file present, restore the kill-switch
  file (or pause that lane) and report it. Everything else is propose-only for owner approval.
- Demo only. Do not point anything that can trade at the live account `121409`.

## Tasks
### T1 — Full terminal/EA inventory (live)
For every running `terminal64.exe`, report: path, login, server, each attached EA + symbol +
timeframe, armed state (`InpDryRunOnly`/`InpBrokerActionAllowed`), and the **timestamp of its
most recent runtime log row** (to prove it is writing *now*, not stale). Cover at minimum:
A1 (`1025742`), A2 (`1033030`, `C:\MT5PortableTier1BestEA`), A3 (`1033669`,
`C:\MT5PortableRepairLane`), every observer terminal, and any terminal on live `121409`.

### T2 — Core trading EAs healthy and active
Confirm, with fresh evidence (log rows / positions dated after the open):
- A2 breakout `Phase2ExperimentalDemoExecutor` (magic 920101): attached, armed, scope-locks
  passing, writing signal rows, current positions/orders.
- A3 `Account3RoundRetestGuardedExecutor` (933000) and `Account3RoundRetestStructuredExecutor`
  (933100): attached on `1033669`, scope-locks passing, writing signal rows.

### T3 — DirectionState publisher + consumers
Confirm the H1 publisher is running and `Common\Files\dirstate_xauusd.csv` has a **fresh**
timestamp, and that A2/A3 new signal/order rows are carrying the `dirstate_*` columns.

### T4 — Observers
Confirm each observer terminal (path observers, shadow-fix, trend-guarded, equity-guardian
shadow, spread logger) is attached and writing — list each with its last log timestamp.

### T5 — Diagnose the runtime-log gap
Determine why runtime signal/order CSVs were unreadable for 90+ minutes
(`RUNTIME_LOGS_MISSING_GT_90_MIN`): stopped terminal, moved/renamed files, decommission
side-effect, permissions, or path mismatch. Fix the monitoring visibility or explain it.

### T6 — Resolve the P2WEAKNESS lane state
The supervisor flags it armed with kill-switch missing, logs gone, and old magic `930101`.
Determine whether this lane is meant to be **running, decommissioned, or stale**. If it is
armed and live, restore its kill switch (or pause it) per the safety exception and report.
State clearly what it currently is and recommend the resolution.

### T7 — Live account `121409` confirmation
List which terminal(s) are logged into `Capital.ComMena-Live 121409` and confirm **none of
them can place trades** (no trading EA, or broker action disabled). Flag anything that can.

## Reporting
Write `LIVE_HEALTH_CHECK_REPORT_2026_06_14.md` with raw command/MT5/log output and a
component-by-component **GREEN / RED** table: A1, A2 breakout, A2 guardian-shadow, A2
DirectionState publisher, A3 RDGUARD, A3 RDSTRUCT, each observer, the dirstate Common file,
the runtime-log pipeline, the P2WEAKNESS lane, and the live-account check. For each RED, give
the cause and the recommended fix (applied only if it falls under the safety exception).
