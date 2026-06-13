# T12 Bar And Shadow Refresh Reverify

Status: `PASS_NO_REGRESSION_WITH_CURRENT_HISTORY_CEILING`

## Review Stop Issue

The NO-GO review reported two regressions:

- `XAUUSD_M5_20260601_to_latest.csv` ended at `2026-06-12 09:15:00` instead of `2026-06-12 20:55:00`.
- `PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv` dropped to 1370 rows and started at `2026-06-03 13:20:00` instead of retaining the `2026-06-01 15:10:00` start.

Those regressions are not present after a guarded scratch export and actual repo re-export.

## Guarded Scratch Export

| Check | Value |
|---|---:|
| Scratch dir | `C:\MT5CompileScratch\T12Reexport_20260614_015040` |
| Requested end UTC | `2026-06-13 21:50:40` |
| XAUUSD M5 rows | 2736 |
| XAUUSD M5 first bar | `2026-06-01 00:00:00` |
| XAUUSD M5 last bar | `2026-06-12 20:55:00` |

The scratch export did not shorten XAUUSD M5 coverage, so the actual repo export was rerun.

## Actual Repo Re-Export

| Artifact | Result |
|---|---|
| Bar export report | `outputs/reports/PHASE2_M5_REPLAY_BAR_EXPORT_REPORT.json` |
| Impulse shadow report | `outputs/reports/PHASE2_IMPULSE_VETO_SHADOW_REPORT.json` |
| Impulse rows CSV | `outputs/reports/PHASE2_IMPULSE_VETO_SHADOW_ROWS.csv` |
| Requested end UTC | `2026-06-13 21:51:43` |
| Shadow status | `SHADOW_READY` |

## Coverage

| Series | Rows | First UTC | Last UTC |
|---|---:|---|---|
| XAUUSD M5 | 2736 | `2026-06-01 00:00:00` | `2026-06-12 20:55:00` |
| XAUUSD H1 | 228 | `2026-06-01 00:00:00` | `2026-06-12 20:00:00` |
| XAUUSD H4 | 61 | `2026-06-01 00:00:00` | `2026-06-12 20:00:00` |
| XAUUSD D1 | 11 | `2026-06-01 00:00:00` | `2026-06-12 00:00:00` |
| USDJPY M5 | 2836 | `2026-06-01 00:00:00` | `2026-06-12 20:55:00` |

USDJPY M5 advanced from the prior `2026-06-12 09:45:00` endpoint to `2026-06-12 20:55:00`.

## Impulse Shadow Rows

| Check | Value |
|---|---:|
| Rows | 1510 |
| Minimum entry time | `2026-06-01 15:10:00` |
| Maximum entry time | `2026-06-13 00:15:01` |
| First row entry time | `2026-06-13 00:15:01` |
| Last row entry time | `2026-06-01 15:10:00` |

## Current History Ceiling

The fresh Sunday MT5 export requested history through `2026-06-13 21:51:43` UTC, but XAUUSD M5 still stops at `2026-06-12 20:55:00` UTC. This report does not claim bars past that timestamp. Treat `2026-06-12 20:55:00` as the current broker-history ceiling until a post-close or new-session export proves otherwise.

## Boundary

- Read-only history export and shadow report generation only.
- No orders, positions, charts, profiles, presets, or EA settings changed.
- The Monday attach gate remains closed.

## Result

T12 has been rerun without the reported M5/shadow regression. The repo now carries refreshed export metadata and USDJPY M5 catch-up rows; XAUUSD M5 remains capped at the latest broker-provided Friday close bar.
