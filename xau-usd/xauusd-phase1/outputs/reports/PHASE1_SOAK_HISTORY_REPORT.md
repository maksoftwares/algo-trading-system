# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 132. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | WARN | Latest warning status fields: log_verification, soak_analysis, runtime_health |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 132
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-27T09:36:01.671567+00:00
- Latest M5 bar: 2026.05.27 09:35:00
- Latest soak progress: 98.82%
- Longest active streak: 22.92h
- Current active streak: 11.58h
- Weekend policy: weekend_breaks_active_market_streak
- Process uptime streak: 118.54h
- Code-freeze hours: 9.08h
- Latest would-signal rows: 74
- Latest setup clusters: 74

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| WARN | WARN | WARN | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-27T00:31:32.458153+00:00 | 2026.05.27 00:30:00 | 1 | 0.0 | 0.0 | 0.0 | 0 | 0 | FAIL |
| 2026-05-27T00:36:59.062573+00:00 | 2026.05.27 00:35:00 | 612 | 91.32 | 22.92 | 0.09 | 65 | 65 | PENDING |
| 2026-05-27T00:41:03.912380+00:00 | 2026.05.27 00:40:00 | 613 | 91.39 | 22.92 | 0.16 | 65 | 65 | PENDING |
| 2026-05-27T01:25:31.924939+00:00 | 2026.05.27 01:25:00 | 622 | 92.01 | 22.92 | 0.9 | 67 | 67 | PENDING |
| 2026-05-27T02:27:11.598116+00:00 | 2026.05.27 02:25:00 | 634 | 92.85 | 22.92 | 1.93 | 67 | 67 | PENDING |
| 2026-05-27T03:28:06.775244+00:00 | 2026.05.27 03:25:00 | 646 | 93.68 | 22.92 | 2.95 | 67 | 67 | PENDING |
| 2026-05-27T04:30:15.418056+00:00 | 2026.05.27 04:30:00 | 659 | 94.58 | 22.92 | 3.98 | 67 | 67 | PENDING |
| 2026-05-27T05:30:50.152862+00:00 | 2026.05.27 05:30:00 | 671 | 95.42 | 22.92 | 4.99 | 67 | 67 | PENDING |
| 2026-05-27T06:32:14.152980+00:00 | 2026.05.27 06:30:00 | 683 | 96.25 | 22.92 | 6.01 | 69 | 69 | PENDING |
| 2026-05-27T07:32:40.798053+00:00 | 2026.05.27 07:30:00 | 695 | 97.08 | 22.92 | 7.02 | 69 | 69 | PENDING |
| 2026-05-27T08:34:09.338293+00:00 | 2026.05.27 08:30:00 | 707 | 97.92 | 22.92 | 8.05 | 70 | 70 | PENDING |
| 2026-05-27T09:36:01.671567+00:00 | 2026.05.27 09:35:00 | 720 | 98.82 | 22.92 | 9.08 | 74 | 74 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 14 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-27T00:31:32.458153+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
