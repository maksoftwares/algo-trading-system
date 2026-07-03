# Observer Heartbeat Report

Status: `PASS`

Read-only heartbeat report. It checks observer CSV freshness and row counts only; it does not touch MT5 terminals, charts, EA inputs, orders, or positions.

Generated at UTC: `2026-07-01T00:14:07.397392Z`

## Lanes

| Lane | Status | Files | Latest age min | Latest file |
| --- | --- | ---: | ---: | --- |
| shadow_fix_observers | PASS | 14 | 4.1 | `shadow_fix_observer_signal_log_symbol_normalized_round_retest_v0_usdjpy.csv` |
| trend_guarded_fix_observers | PASS | 14 | 4.13 | `trend_guarded_fix_observer_v2_signal_log_symbol_normalized_round_retest_v0_eurusd.csv` |
| position_path_observer | PASS | 3 | 0.99 | `position_path_observer_startup.csv` |

## Checks

### shadow_fix_observers

| Check | Status | Detail |
| --- | --- | --- |
| files_present | PASS | 14 files found, expected at least 14 |
| latest_file_fresh | PASS | latest age 4.1 minutes; threshold 15 minutes |

### trend_guarded_fix_observers

| Check | Status | Detail |
| --- | --- | --- |
| files_present | PASS | 14 files found, expected at least 14 |
| latest_file_fresh | PASS | latest age 4.1 minutes; threshold 15 minutes |

### position_path_observer

| Check | Status | Detail |
| --- | --- | --- |
| files_present | PASS | 3 files found, expected at least 3 |
| latest_file_fresh | PASS | latest age 1.0 minutes; threshold 15 minutes |

## Boundary

- This report is monitoring-only.
- It does not restart terminals.
- It does not attach or remove EAs.
- It does not modify running demo EAs, orders, positions, presets, profiles, or charts.
