# T12 Bar And Shadow Refresh Reverify2

Status: `PASS_NO_REGRESSION_CURRENT_HISTORY_CEILING`

This report supersedes `PHASE2_T12_BAR_SHADOW_REFRESH_REVERIFY_2026_06_14.md`.

## Global Boundaries

- A3 demo login `1033669`.
- A2 (`1033030`) untouched.
- A1 (`1025742`) touched only for the T0 mutex fix.
- Demo only; no live trading; canonical Phase 2 status unchanged.
- All committed defaults remain non-executing: `InpDryRunOnly=true`, `InpBrokerActionAllowed=false`.
- A3 combined preflight and attach status remain `DO_NOT_ATTACH`.

## Start Checkout State

Raw output from `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system`:

```text
COMMAND: git rev-parse --show-toplevel
C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system
COMMAND: git rev-parse HEAD
1d6962dfffca75cd5461251569c7251b1e27cc48
COMMAND: git status --porcelain
 M status.html
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.md
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.md
?? CODEX_ADDENDUM_EVENING_SESSION_AND_CONFLUENCE_2026_06_13.md
?? CODEX_WORK_ORDER_A3_REPAIR_LANE_2026_06_13.md
?? CODEX_WORK_ORDER_ADDENDUM2_EAT2_EAT3PREP_2026_06_13.md
?? CODEX_WORK_ORDER_T0_T12_REVERIFY_DISCREPANCY_2026_06_14.md
?? DEEP_DIVE_PROFIT_DUPLICATION_AND_CONSENSUS_2026_06_13.md
?? EVENING_SESSION_POSITIVE_GOAL_PLAN_2026_06_13.md
?? PORTFOLIO_AND_FIXED_EA_DEPLOYMENT_PLAN_2026_06_13.md
COMMAND: Get-Date / UTC now
2026-06-14 02:04:08 +04:00
2026-06-13T22:04:08Z
```

## Pre-Export Coverage In This Checkout

Raw output from `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1`:

```text
outputs\reports\m5_replay_bars\XAUUSD_M5_20260601_to_latest.csv
rows 2736
first 2026-06-01 00:00:00
last 2026-06-12 20:55:00
outputs\reports\PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv
rows 1510
min_entry 2026-06-01 15:10:00
max_entry 2026-06-13 00:15:01
first_row_entry 2026-06-13 00:15:01
last_row_entry 2026-06-01 15:10:00
```

## Export Commands

Raw output:

```text
COMMAND: ..\xauusd-phase0\.venv\Scripts\python.exe scripts\export_phase2_m5_replay_bars.py --symbols XAUUSD EURUSD GBPUSD USDJPY --timeframes M5 H1 H4 D1 --start '2026-06-01 00:00:00'
C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_M5_REPLAY_BAR_EXPORT_REPORT.json
COMMAND: ..\xauusd-phase0\.venv\Scripts\python.exe scripts\generate_phase2_impulse_veto_shadow_report.py
Status: SHADOW_READY
JSON: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_IMPULSE_VETO_SHADOW_REPORT.json
Markdown: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_IMPULSE_VETO_SHADOW_REPORT.md
Rows CSV: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv
Resolved closed rows: 1502
```

The export was requested at current local session time `2026-06-14 02:04:08 +04:00`, which is `2026-06-13T22:04:08Z`.

## Pandas Coverage Check

The requested `python3` interpreter is not usable on this Windows checkout:

```text
COMMAND: python3 pandas coverage check (requested interpreter)
Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases.
```

Equivalent repo venv command actually run:

```text
..\xauusd-phase0\.venv\Scripts\python.exe pandas coverage check
```

Raw output:

```text
COMMAND: ..\xauusd-phase0\.venv\Scripts\python.exe pandas coverage check
(2736, 12) 2026-06-01 00:00:00 2026-06-12 20:55:00
(1510, 24) 2026-06-01 15:10:00 2026-06-13 00:15:01
```

Result: the shadow file minimum entry time is at the required prior front boundary `2026-06-01 15:10:00`, and XAUUSD M5 extends to the prior confirmed ceiling `2026-06-12 20:55:00`.

## Export Tool Latest-Available Evidence

Raw excerpt from `outputs/reports/PHASE2_M5_REPLAY_BAR_EXPORT_REPORT.json` after the rerun:

```json
{
  "status": "PASS",
  "created_at_utc": "2026-06-13T22:04:21.720194Z",
  "requested_start_utc": "2026-06-01 00:00:00",
  "requested_end_utc": "2026-06-13 22:04:21",
  "source": {
    "terminal_exe": "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
    "mode": "read_only_history_copy_rates_range",
    "symbol_select_used": false,
    "chart_or_order_changes": false,
    "terminal_data_path": "C:\\Users\\ZHAO ZHU INFORMATION\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF075",
    "account_login_masked": "10***42",
    "account_server": "Capital.ComMena-Demo"
  },
  "XAUUSD_M5": {
    "symbol": "XAUUSD",
    "timeframe": "M5",
    "status": "WARN_GAPS_OR_DUPLICATES",
    "rows": 2736,
    "first_bar_utc": "2026-06-01 00:00:00",
    "last_bar_utc": "2026-06-12 20:55:00",
    "requested_start_utc": "2026-06-01 00:00:00",
    "requested_end_utc": "2026-06-13 22:04:21",
    "gap_count_gt_5m": 9,
    "max_gap_minutes": "2945.0",
    "duplicate_bar_times": 0,
    "continuity_pct_from_first_to_last": "80.00"
  }
}
```

Broker history did not provide XAUUSD M5 bars past `2026-06-12 20:55:00` even though the requested end was `2026-06-13 22:04:21` UTC. This report treats `2026-06-12 20:55:00` as the current latest available XAUUSD M5 broker-history ceiling for this export, not as an attach-ready advancement.

## Shadow Report Row Counts

Raw excerpt from `outputs/reports/PHASE2_IMPULSE_VETO_SHADOW_REPORT.md` after the rerun:

```text
# Phase 2 Impulse Veto Shadow Report

Status: `SHADOW_READY`

## Row Counts

| Metric | Value |
|---|---:|
| raw_rows | 1510 |
| closed_rows | 1502 |
| resolved_closed_rows | 1502 |
| target_resolved_closed_rows | 1065 |
| unresolved_rows | 0 |

## Bar Export Quality

| symbol | status | rows | first_bar_utc | last_bar_utc | gap_count_gt_5m | max_gap_minutes | duplicate_bar_times |
|---|---|---|---|---|---|---|---|
| EURUSD | WARN_GAPS_OR_DUPLICATES | 2836 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2885.0000 | 0 |
| GBPUSD | WARN_GAPS_OR_DUPLICATES | 2836 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2885.0000 | 0 |
| USDJPY | WARN_GAPS_OR_DUPLICATES | 2836 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2885.0000 | 0 |
| XAUUSD | WARN_GAPS_OR_DUPLICATES | 2736 | 2026-06-01 00:00:00 | 2026-06-12 20:55:00 | 9 | 2945.0000 | 0 |
```

## Focused Tests

Raw output:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1
collecting ... collected 4 items

tests/test_phase2_m5_replay_bar_export.py::test_m5_replay_bar_export_continuity_reports_gaps_and_duplicates PASSED [ 25%]
tests/test_phase2_m5_replay_bar_export.py::test_m5_replay_bar_export_markdown_states_read_only_boundary PASSED [ 50%]
tests/test_phase2_impulse_veto_shadow_report.py::test_impulse_veto_blocks_weak_family_counter_impulse_only PASSED [ 75%]
tests/test_phase2_impulse_veto_shadow_report.py::test_impulse_veto_report_has_no_runtime_mt5_dependency PASSED [100%]

============================== 4 passed in 0.05s ==============================
```

## Diff Scope After Export

Raw output:

```text
 .../reports/PHASE2_IMPULSE_VETO_SHADOW_REPORT.json |  2 +-
 .../PHASE2_M5_REPLAY_BAR_EXPORT_REPORT.json        | 36 +++++++++++-----------
 .../reports/PHASE2_M5_REPLAY_BAR_EXPORT_REPORT.md  |  2 +-
 3 files changed, 20 insertions(+), 20 deletions(-)
warning: in the working copy of 'xau-usd/xauusd-phase1/outputs/reports/PHASE2_IMPULSE_VETO_SHADOW_REPORT.md', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'xau-usd/xauusd-phase1/outputs/reports/PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'xau-usd/xauusd-phase1/outputs/reports/PHASE2_M5_REPLAY_BAR_EXPORT_REPORT.md', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'xau-usd/xauusd-phase1/outputs/reports/m5_replay_bars/XAUUSD_M5_20260601_to_latest.csv', CRLF will be replaced by LF the next time Git touches it
```

Only export/report metadata changed. The XAUUSD M5 CSV and impulse rows CSV did not change content after this rerun.

## End Checkout State Before This Report Commit

Raw output from `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system`:

```text
COMMAND: git rev-parse --show-toplevel
C:/Users/ZHAO ZHU INFORMATION/Downloads/algo-trading-system
COMMAND: git rev-parse HEAD
1d6962dfffca75cd5461251569c7251b1e27cc48
COMMAND: git status --porcelain
 M status.html
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_FORWARD_WEEK_REPORT.md
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_DEMO_REPAIR_MONITOR_LATEST.md
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_IMPULSE_VETO_SHADOW_REPORT.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_M5_REPLAY_BAR_EXPORT_REPORT.json
 M xau-usd/xauusd-phase1/outputs/reports/PHASE2_M5_REPLAY_BAR_EXPORT_REPORT.md
?? CODEX_ADDENDUM_EVENING_SESSION_AND_CONFLUENCE_2026_06_13.md
?? CODEX_WORK_ORDER_A3_REPAIR_LANE_2026_06_13.md
?? CODEX_WORK_ORDER_ADDENDUM2_EAT2_EAT3PREP_2026_06_13.md
?? CODEX_WORK_ORDER_T0_T12_REVERIFY_DISCREPANCY_2026_06_14.md
?? DEEP_DIVE_PROFIT_DUPLICATION_AND_CONSENSUS_2026_06_13.md
?? EVENING_SESSION_POSITIVE_GOAL_PLAN_2026_06_13.md
?? PORTFOLIO_AND_FIXED_EA_DEPLOYMENT_PLAN_2026_06_13.md
```

## Result

T12 was rerun in this checkout without dropping front history or falling below the prior confirmed XAUUSD M5 ceiling. XAUUSD M5 remains at 2736 rows from `2026-06-01 00:00:00` through `2026-06-12 20:55:00`; shadow rows remain 1510 rows from `2026-06-01 15:10:00` through `2026-06-13 00:15:01`. The Monday A3 attach gate remains closed.
