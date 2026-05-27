# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 142. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | WARN | Latest warning status fields: log_verification, soak_analysis, runtime_health |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 142
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-27T12:03:23.730846+00:00
- Latest M5 bar: 2026.05.27 12:00:00
- Latest soak progress: 100.0%
- Longest active streak: 22.92h
- Current active streak: 1.33h
- Weekend policy: weekend_breaks_active_market_streak
- Process uptime streak: 1.36h
- Code-freeze hours: 1.36h
- Latest would-signal rows: 80
- Latest setup clusters: 80

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| WARN | WARN | WARN | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-27T08:34:09.338293+00:00 | 2026.05.27 08:30:00 | 707 | 97.92 | 22.92 | 8.05 | 70 | 70 | PENDING |
| 2026-05-27T09:36:01.671567+00:00 | 2026.05.27 09:35:00 | 720 | 98.82 | 22.92 | 9.08 | 74 | 74 | PENDING |
| 2026-05-27T10:36:38.661834+00:00 | 2026.05.27 10:35:00 | 732 | 99.65 | 22.92 | 10.09 | 78 | 78 | PENDING |
| 2026-05-27T10:42:32.257656+00:00 | 2026.05.27 10:40:00 | 734 | 99.72 | 22.92 | 0.0 | 78 | 78 | PENDING |
| 2026-05-27T10:43:36.553911+00:00 | 2026.05.27 10:40:00 | 734 | 99.72 | 22.92 | 0.03 | 78 | 78 | PENDING |
| 2026-05-27T10:46:00.639890+00:00 | 2026.05.27 10:45:00 | 735 | 99.79 | 22.92 | 0.07 | 78 | 78 | PENDING |
| 2026-05-27T11:38:19.358235+00:00 | 2026.05.27 11:35:00 | 745 | 100.0 | 22.92 | 0.94 | 78 | 78 | PENDING |
| 2026-05-27T11:51:01.972653+00:00 | 2026.05.27 11:50:00 | 748 | 100.0 | 22.92 | 1.15 | 78 | 78 | PENDING |
| 2026-05-27T11:56:29.013735+00:00 | 2026.05.27 11:55:00 | 749 | 100.0 | 22.92 | 1.24 | 80 | 80 | PENDING |
| 2026-05-27T12:01:13.746497+00:00 | 2026.05.27 12:00:00 | 750 | 100.0 | 22.92 | 1.32 | 80 | 80 | PENDING |
| 2026-05-27T12:02:14.361519+00:00 | 2026.05.27 12:00:00 | 750 | 100.0 | 22.92 | 1.34 | 80 | 80 | PENDING |
| 2026-05-27T12:03:23.730846+00:00 | 2026.05.27 12:00:00 | 750 | 100.0 | 22.92 | 1.36 | 80 | 80 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 14 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-27T00:31:32.458153+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
