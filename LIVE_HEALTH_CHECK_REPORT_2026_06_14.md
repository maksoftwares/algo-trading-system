# Live Health Check Report - 2026-06-14 Sunday Open

Generated: 2026-06-15 02:27 Dubai time  
Scope: read-only MT5/runtime health check, demo lanes plus live-account safety check.  
Work order: `CODEX_WORK_ORDER_LIVE_HEALTH_CHECK_2026_06_14.md`

## Executive Result

Overall status: AMBER

The live rig is mostly running and writing fresh logs after the Sunday market open. A1, A2, A3, Phase 1 dry-run, A1 position-path observer, shadow-fix observers, trend-guarded observers, A2 equity guardian, and live spread logger all have fresh post-open evidence.

Two issues remain:

1. The supervisor RED condition is a monitoring-scope problem, not proof that the active EAs stopped. It is still watching the old/decommissioned P2Weakness/canonical lane while A1/A2/A3 logs are live.
2. The DirectionState publisher is writing the common file now, but the state payload still references the last closed XAUUSD H1 bar from 2026.06.12 20:00 UTC. Treat DirectionState as live transport but stale/inconclusive state data until it advances after the first fresh H1 close.

No live-capital broker-action EA was found from file/log evidence. Direct MT5 bridge verification was not available because the local Python runtime does not have the `MetaTrader5` module installed.

## Component Table

| Component | Status | Evidence | Notes |
|---|---|---|---|
| A1 standard demo terminal `1025742` | GREEN | Running process `C:\Program Files\MetaTrader 5\terminal64.exe`; data dir `D0E820...`; signal rows through `2026.06.14 22:25 UTC` | Broker-action demo EAs are writing. Order rows after open exist on EURUSD/GBPUSD. |
| A2 breakout `1033030` | GREEN | `C:\MT5PortableTier1BestEA`; `tier1_bestea_signal_log_xauusd.csv` through `2026.06.14 22:25 UTC` | Armed demo lane, XAUUSD only. Guardian shows 0 open positions at latest sample. |
| A2 equity guardian shadow | GREEN | `A2_EQUITY_GUARDIAN_SHADOW_LOG.csv` through `2026.06.14 22:25 UTC` | Observer/shadow only. |
| A2 DirectionState publisher | AMBER | `Common\Files\dirstate_xauusd.csv` LastWriteTime `2026-06-15 02:24:53 Dubai` | File is refreshing, but row payload is H1 bar `2026.06.12 20:00 UTC`. Wait for fresh H1 close. |
| A3 RDGUARD `1033669` | GREEN | `C:\MT5PortableRepairLane`; `a3_rdguard_v1_signal_log.csv` through `2026.06.14 22:25 UTC` | Armed demo lane, XAUUSD, magic `933000`; no order rows after attach except header. |
| A3 RDSTRUCT `1033669` | GREEN | `C:\MT5PortableRepairLane`; `a3_rdstruct_v1_signal_log.csv` through `2026.06.14 22:25 UTC` | Armed demo lane, XAUUSD, magic `933100`; no order rows after attach except header. |
| A1 position-path observer | GREEN | `C:\MT5PortablePositionPathObserver`; `position_path_log_20260615.csv` through `2026.06.14 22:27 UTC` | Capturing live open-position paths on account `1025742`. |
| A2/Tier1 path observer | AMBER | `C:\MT5PortableTier1PathObserver` process running; startup shows `REMOVED_REASON_8`; no fresh path rows | Likely no active observer chart. Also logged on live account `121409`, so keep passive only. |
| Shadow-fix observers | GREEN | `C:\MT5PortableShadowFixObservers`; 14 startup files; signal logs through `2026.06.15 02:24 Dubai` | Telemetry-only, `broker_action_allowed=false`. |
| Trend-guarded observers | GREEN | `C:\MT5PortableTrendGuardedFixObservers`; 14 startup files; signal logs through `2026.06.15 02:24 Dubai` | Telemetry-only, `broker_action_allowed=false`. |
| Phase 1 dry-run / GoldMission | GREEN | `C:\MT5PortableGoldMission`; `decision_log.csv` through `2026.06.14 22:25 UTC` | Dry-run only; `phase1_dry_run_only` block reason. |
| Spread logger live `121409` | GREEN | `C:\MT5PortableSpreadLogger`; `spread_log_121409_Capital.ComMena-Live_XAUUSD_20260614.csv` through `2026.06.14 22:26 UTC` | Passive spread logging on live account. No order log evidence. |
| Runtime-log supervisor pipeline | RED | Supervisor watched old P2Weakness/canonical lane; active A1/A2/A3 logs are fresh | Fix monitoring inputs to include A1/A2/A3/DirectionState/current observer lanes. |
| P2Weakness old lane `930101` | GREEN for runtime safety, RED for stale monitor scope | No running `terminal64.exe` from P2Weakness paths; logs moved to `_codex_quarantine`; cleanup report says old magic has no open positions/orders | Do not restart. Supervisor should stop treating this as active. |
| Live account `121409` safety | AMBER | Spread logger fresh on live account; Tier1PathObserver terminal also logged live but observer removed | No trading EA evidence found, but direct MT5 bridge query unavailable. |

## Running Terminal Inventory

Command:

```powershell
Get-Process terminal64 -ErrorAction SilentlyContinue | Select-Object Id,Path,StartTime
```

Observed running terminals:

| Process | Path | Start time | Interpreted role |
|---:|---|---|---|
| 3144 | `C:\MT5PortableShadowFixObservers\terminal64.exe` | 2026-06-13 02:54:46 | Shadow-fix observer terminal |
| 6856 | `C:\MT5PortableTier1PathObserver\terminal64.exe` | 2026-06-14 20:39:20 | Tier1 path observer terminal, not writing fresh path rows |
| 11724 | `C:\MT5PortablePositionPathObserver\terminal64.exe` | 2026-06-13 02:54:46 | A1 position-path observer |
| 16092 | `C:\MT5PortableSpreadLogger\terminal64.exe` | 2026-06-13 02:54:46 | Live account spread logger |
| 17200 | `C:\MT5PortableTrendGuardedFixObservers\terminal64.exe` | 2026-06-13 02:54:46 | Trend-guarded observer terminal |
| 17524 | `C:\MT5PortableTier1BestEA\terminal64.exe` | 2026-06-14 20:39:20 | A2 breakout + guardian + DirectionState |
| 17676 | `C:\Program Files\MetaTrader 5\terminal64.exe` | 2026-06-14 00:18:49 | A1 standard demo broker-action terminal |
| 21248 | `C:\MT5PortableGoldMission\terminal64.exe` | 2026-06-13 02:54:44 | Phase 1 dry-run/passive lane |
| 21676 | `C:\MT5PortableRepairLane\terminal64.exe` | 2026-06-14 20:40:30 | A3 repair lane |

No running process path matched `*P2Weakness*`.

## A1 Standard Demo Evidence

Data directory:

```text
C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files
```

Fresh signal evidence:

```text
experimental_demo_executor_signal_log_v02_breakout_retest_xauusd.csv
latest rows: 2026.06.14 22:20:00 and 2026.06.14 22:25:00 UTC
dry_run=false, broker_action_allowed=true, observer_supported=true
```

Fresh order evidence after open:

```text
experimental_demo_executor_order_log_v02_symbol_normalized_round_retest_v0_eurusd.csv
2026.06.14 22:05:00 UTC ORDER_SEND_OK LONG 0.05 EURUSD
2026.06.14 22:10:00 UTC ORDER_SEND_OK LONG 0.05 EURUSD
```

Family mutex evidence after open:

```text
experimental_demo_executor_order_log_v02_swing_breakout_retest_v0_gbpusd.csv
2026.06.14 21:40:05 UTC GUARD_BLOCK SHORT guard_reason=WOULD_DUPLICATE_FAMILY_EVENT
```

Finding: A1 is active and writing. Its current standard executor logs do not yet include `dirstate_*` columns. The DirectionState shadow work is currently proven on A2/A3, not A1.

## A2 Breakout Evidence

Terminal:

```text
C:\MT5PortableTier1BestEA
```

Startup rows:

```text
account_server=Capital.ComMena-Demo
account_login=1033030
symbol=XAUUSD
candidate=breakout_retest
dry_run=false
broker_action_allowed=true
kill_switch_file=tier1_bestea_kill_switch.txt
status=ATTACHED_DEMO_EXECUTOR_ENABLED
```

Latest signal row:

```text
2026.06.14 22:25:01 broker
2026.06.14 22:24:59 UTC
2026.06.15 02:24:59 Dubai
stage=WAIT_LEVEL_BREAK_RETEST
direction=SHORT
would_signal=false
reason=no_short_breakout_retest_candidate
dirstate_direction=0
dirstate_regime=FLAT
dirstate_strength=0.010
```

Guardian latest row:

```text
2026.06.14 22:25:05 UTC
equity=4055.21
open_positions=0
status=NONE
```

Finding: A2 is attached, armed, and writing. No A2 order rows after Sunday open were observed in `tier1_bestea_order_log_xauusd.csv`; latest order rows are older guard blocks from 2026-06-12.

## A3 Repair Lane Evidence

Terminal:

```text
C:\MT5PortableRepairLane
```

RDGUARD latest startup:

```text
A3_RDGUARD_V1_SAFE
Capital.ComMena-Demo
account_login=1033669
symbol=XAUUSD
magic=933000
dry_run=false
broker_action_allowed=true
status=ATTACHED_A3_RDGUARD_V1
```

RDSTRUCT latest startup:

```text
A3_RDSTRUCT_V1_SAFE
Capital.ComMena-Demo
account_login=1033669
symbol=XAUUSD
magic=933100
dry_run=false
broker_action_allowed=true
status=ATTACHED_A3_RDSTRUCT_V1
```

Fresh signal rows:

```text
a3_rdguard_v1_signal_log.csv latest row:
2026.06.14 22:25:00 UTC, would_signal=false, dirstate_direction=0, dirstate_regime=FLAT

a3_rdstruct_v1_signal_log.csv latest row:
2026.06.14 22:25:00 UTC, would_signal=false, dirstate_direction=0, dirstate_regime=FLAT
```

Order logs:

```text
a3_rdguard_v1_order_log.csv: header only
a3_rdstruct_v1_order_log.csv: header only
```

Finding: A3 is attached, armed, scope-locked by startup evidence, and writing fresh signal rows. No post-attach order sends have occurred.

## DirectionState Publisher And Consumers

Common file:

```text
C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\Common\Files\dirstate_xauusd.csv
LastWriteTime: 2026-06-15 02:24:53 Dubai
```

Latest state row:

```text
utc_time=2026.06.12 20:00:00
dubai_time=2026.06.13 00:00:00
direction=0
regime=FLAT
strength=0.010
```

Consumer column proof:

```text
C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_signal_log_xauusd.csv
columns include dirstate_direction,dirstate_regime,dirstate_strength

C:\MT5PortableRepairLane\MQL5\Files\a3_rdguard_v1_signal_log.csv
columns include dirstate_direction,dirstate_regime,dirstate_strength

C:\MT5PortableRepairLane\MQL5\Files\a3_rdstruct_v1_signal_log.csv
columns include dirstate_direction,dirstate_regime,dirstate_strength
```

Finding: transport is live and consumers are logging the fields. The state bar timestamp is stale. Do not use DirectionState for any decision; keep it shadow-only and verify it advances after the next broker H1 close.

## Observer Evidence

| Observer | Status | Latest evidence |
|---|---|---|
| A1 position-path observer | GREEN | `position_path_log_20260615.csv` latest row `2026.06.14 22:27:19 UTC` |
| Shadow-fix observers | GREEN | 14 startup files; signal logs through `2026.06.15 02:24 Dubai` |
| Trend-guarded observers | GREEN | 14 startup files; signal logs through `2026.06.15 02:24 Dubai` |
| A2 equity guardian shadow | GREEN | `A2_EQUITY_GUARDIAN_SHADOW_LOG.csv` through `2026.06.14 22:25 UTC` |
| Tier1 path observer | AMBER | process running, startup shows `REMOVED_REASON_8`, no fresh position-path rows |
| Spread logger | GREEN | live spread log through `2026.06.14 22:26 UTC` |

## Runtime Log Gap Diagnosis

Original RED:

```text
RUNTIME_LOGS_MISSING_GT_90_MIN
```

Cause:

The supervisor was looking at old P2Weakness/canonical runtime paths. Those logs are intentionally stale because P2Weakness was decommissioned/quarantined. Current runtime lanes are writing fresh logs:

```text
A1 standard terminal: signal logs through 2026.06.14 22:25 UTC
A2 Tier1BestEA: signal log through 2026.06.14 22:25 UTC
A3 RepairLane: signal logs through 2026.06.14 22:25 UTC
Phase 1 GoldMission: decision_log through 2026.06.14 22:25 UTC
PositionPathObserver: position_path_log through 2026.06.14 22:27 UTC
SpreadLogger: live spread log through 2026.06.14 22:26 UTC
```

Recommended fix:

Update the hourly supervisor to watch:

```text
A1: D0E820...\MQL5\Files\experimental_demo_executor_signal_log_v02_*.csv
A2: C:\MT5PortableTier1BestEA\MQL5\Files\tier1_bestea_signal_log_xauusd.csv
A2 Guardian: C:\MT5PortableTier1BestEA\MQL5\Files\A2_EQUITY_GUARDIAN_SHADOW_LOG.csv
A3: C:\MT5PortableRepairLane\MQL5\Files\a3_rdguard_v1_signal_log.csv
A3: C:\MT5PortableRepairLane\MQL5\Files\a3_rdstruct_v1_signal_log.csv
DirectionState: Common\Files\dirstate_xauusd.csv plus payload timestamp
Position path: C:\MT5PortablePositionPathObserver\MQL5\Files\position_path_log_YYYYMMDD.csv
Shadow observers: C:\MT5PortableShadowFixObservers\MQL5\Files\shadow_fix_observer_signal_log_*.csv
Trend observers: C:\MT5PortableTrendGuardedFixObservers\MQL5\Files\trend_guarded_fix_observer_v2_signal_log_*.csv
Spread logger: C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_*.csv
```

## P2Weakness Lane State

Status: decommissioned/stale supervisor target.

Evidence:

```text
Get-Process terminal64 | Where-Object Path -like '*P2Weakness*'
result: no running process
```

Runtime files:

```text
C:\MT5PortableP2WeaknessDemo\_codex_quarantine\a3_decommission_20260614_005622\p2weakness_br_v1_signal_log_xauusd.csv
C:\MT5PortableP2WeaknessDemo\_codex_quarantine\a3_decommission_20260614_005622\p2weakness_br_v1_order_log_xauusd.csv
C:\MT5PortableP2WeaknessDemo\_codex_quarantine\a3_decommission_20260614_005622\p2weakness_br_v1_startup_xauusd.csv
```

Prior cleanup report excerpt:

```text
old_magic_930101_positions_closed_or_absent = PASS
old_magic_930101_orders_closed_or_absent = PASS
old_magic_930101_charts_detached_or_absent = PASS
```

Kill switch:

```text
C:\MT5PortableP2WeaknessDemo\MQL5\Files\p2weakness_br_v1_kill_switch.txt: absent
```

No safety-restoring action was applied because the lane is not running. Creating a kill-switch file in a decommissioned, non-running terminal would not change live safety and would blur evidence. Recommended resolution: remove P2Weakness from active supervisor scope or mark it explicitly decommissioned.

## Live Account 121409 Check

Live-account evidence found:

1. `C:\MT5PortableSpreadLogger` writes:

```text
spread_log_121409_Capital.ComMena-Live_XAUUSD_20260614.csv
latest row: 2026.06.14 22:26:13 broker / 22:26:11 UTC / 2026.06.15 02:26:11 Dubai
```

2. `C:\MT5PortableTier1PathObserver` startup rows show:

```text
Capital.ComMena-Live
account_login=121409
status=REMOVED_REASON_8
```

No live-account trading EA order log was found in the inspected live-account terminal evidence. The live spread logger is passive. The Tier1 path observer terminal is running but not writing fresh observer rows and its latest startup status shows removed.

Limitation:

Direct `positions_get()` / `orders_get()` was not run because `MetaTrader5` Python module is not installed in the available Python runtime.

## Actions Taken

No runtime settings were changed.

No kill-switch file was created because no running armed P2Weakness terminal was found.

## Recommended Next Actions

1. Update the hourly supervisor to current A1/A2/A3/observer log paths.
2. Add a DirectionState payload-age check: file timestamp alone is insufficient; the embedded `utc_time` must advance after broker H1 closes.
3. Either detach/close `C:\MT5PortableTier1PathObserver` or reattach it intentionally as a passive observer, because it is currently a running live-account terminal with no fresh observer rows.
4. Install or vendor a controlled MT5 Python bridge environment for read-only `positions_get()` / `orders_get()` checks, or document that live checks are file/log based only.
5. Keep P2Weakness marked decommissioned and remove it from active RED/health scoring.
