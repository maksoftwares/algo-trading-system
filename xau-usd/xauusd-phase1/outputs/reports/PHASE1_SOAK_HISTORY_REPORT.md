# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 99. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | WARN | Latest warning status fields: log_verification, soak_analysis, runtime_health |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 99
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-25T14:02:28.353298+00:00
- Latest M5 bar: 2026.05.25 14:00:00
- Latest soak progress: 62.5%
- Longest active streak: 13.92h
- Current active streak: 13.92h
- Weekend policy: weekend_breaks_active_market_streak
- Process uptime streak: 76.48h
- Code-freeze hours: 28.42h
- Latest would-signal rows: 18
- Latest setup clusters: 18

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| WARN | WARN | WARN | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-23T19:51:44.757694+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-23T20:15:42.025150+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-23T20:16:58.420942+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-23T20:17:27.724940+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-24T09:33:13.629126+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-24T09:37:41.338226+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-24T10:33:52.742753+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.94 | 10 | 10 | PENDING |
| 2026-05-24T11:34:48.288414+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 1.95 | 10 | 10 | PENDING |
| 2026-05-25T12:38:30.000370+00:00 | 2026.05.25 12:35:00 | 232 | 61.32 | 12.5 | 27.02 | 14 | 14 | FAIL |
| 2026-05-25T12:40:38.064511+00:00 | 2026.05.25 12:40:00 | 233 | 61.39 | 12.58 | 27.05 | 14 | 14 | PENDING |
| 2026-05-25T14:01:23.483621+00:00 | 2026.05.25 14:00:00 | 249 | 62.5 | 13.92 | 28.4 | 18 | 18 | PENDING |
| 2026-05-25T14:02:28.353298+00:00 | 2026.05.25 14:00:00 | 249 | 62.5 | 13.92 | 28.42 | 18 | 18 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 7 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-25T12:38:30.000370+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
