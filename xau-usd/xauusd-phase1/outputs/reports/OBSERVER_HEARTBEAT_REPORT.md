# Observer Heartbeat Report

Status: `PASS`

Read-only heartbeat report. It checks observer CSV freshness and row counts only; it does not touch MT5 terminals, charts, EA inputs, orders, or positions.

Generated at UTC: `2026-06-12T09:21:17.983997Z`

## Lanes

| Lane | Status | Files | Latest age min | Latest file |
| --- | --- | ---: | ---: | --- |
| shadow_fix_observers | PASS | 14 | 1.35 | `shadow_fix_observer_signal_log_breakout_retest_xauusd.csv` |
| trend_guarded_fix_observers | PASS | 14 | 0.57 | `trend_guarded_fix_observer_v2_signal_log_session_extreme_retest_v0_xauusd.csv` |
| position_path_observer | PASS | 3 | 0.02 | `position_path_log_20260612.csv` |

## Checks

### shadow_fix_observers

| Check | Status | Detail |
| --- | --- | --- |
| files_present | PASS | 14 files found, expected at least 14 |
| latest_file_fresh | PASS | latest age 1.3 minutes; threshold 15 minutes |

### trend_guarded_fix_observers

| Check | Status | Detail |
| --- | --- | --- |
| files_present | PASS | 14 files found, expected at least 14 |
| latest_file_fresh | PASS | latest age 0.6 minutes; threshold 15 minutes |

### position_path_observer

| Check | Status | Detail |
| --- | --- | --- |
| files_present | PASS | 3 files found, expected at least 3 |
| latest_file_fresh | PASS | latest age 0.0 minutes; threshold 15 minutes |

## Boundary

- This report is monitoring-only.
- It does not restart terminals.
- It does not attach or remove EAs.
- It does not modify running demo EAs, orders, positions, presets, profiles, or charts.
