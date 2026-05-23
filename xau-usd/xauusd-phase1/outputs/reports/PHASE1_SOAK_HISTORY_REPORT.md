# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 91. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | PASS | Latest status is healthy; acceptance is PENDING. |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 91
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-23T20:17:27.724940+00:00
- Latest M5 bar: 2026.05.22 20:55:00
- Latest soak progress: 8.26%
- Longest active streak: 2.25h
- Current active streak: 0.0h
- Weekend policy: weekend_breaks_active_market_streak
- Process uptime streak: 34.73h
- Code-freeze hours: 0.0h
- Latest would-signal rows: 10
- Latest setup clusters: 10

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-23T17:50:03.690843+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 |  | 10 | 10 | PENDING |
| 2026-05-23T17:59:11.447398+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 |  | 10 | 10 | PENDING |
| 2026-05-23T18:04:53.181536+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 |  | 10 | 10 | PENDING |
| 2026-05-23T18:33:31.442130+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-23T18:35:02.719031+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-23T19:08:57.129583+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-23T19:36:24.285969+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-23T19:36:37.171883+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-23T19:51:44.757694+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-23T20:15:42.025150+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-23T20:16:58.420942+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |
| 2026-05-23T20:17:27.724940+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 2.25 | 0.0 | 10 | 10 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 6 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-23T13:25:05.558361+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
