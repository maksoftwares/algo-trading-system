# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 177. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | PASS | Latest status is healthy; acceptance is PENDING. |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 177
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-28T14:16:29.342518+00:00
- Latest M5 bar: 2026.05.28 14:15:00
- Latest soak progress: 100.0%
- Longest active streak: 53.92h
- Current active streak: 26.5h
- Weekend policy: expected_market_breaks_pause_active_market_streak
- Process uptime streak: 27.58h
- Code-freeze hours: 27.58h
- Latest would-signal rows: 118
- Latest setup clusters: 118

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-28T13:32:43.510625+00:00 | 2026.05.28 13:30:00 | 1044 | 100.0 | 53.92 | 26.85 | 118 | 118 | PENDING |
| 2026-05-28T13:39:28.867803+00:00 | 2026.05.28 13:35:00 | 1045 | 100.0 | 53.92 | 26.96 | 118 | 118 | PENDING |
| 2026-05-28T13:46:59.991458+00:00 | 2026.05.28 13:45:00 | 1047 | 100.0 | 53.92 | 27.09 | 118 | 118 | PENDING |
| 2026-05-28T13:48:11.499052+00:00 | 2026.05.28 13:45:00 | 1047 | 100.0 | 53.92 | 27.11 | 118 | 118 | PENDING |
| 2026-05-28T13:54:25.258338+00:00 | 2026.05.28 13:50:00 | 1048 | 100.0 | 53.92 | 27.21 | 118 | 118 | PENDING |
| 2026-05-28T13:59:33.261969+00:00 | 2026.05.28 13:55:00 | 1049 | 100.0 | 53.92 | 27.3 | 118 | 118 | PENDING |
| 2026-05-28T14:02:33.228906+00:00 | 2026.05.28 14:00:00 | 1050 | 100.0 | 53.92 | 27.35 | 118 | 118 | PENDING |
| 2026-05-28T14:05:27.636403+00:00 | 2026.05.28 14:05:00 | 1051 | 100.0 | 53.92 | 27.39 | 118 | 118 | PENDING |
| 2026-05-28T14:08:03.005680+00:00 | 2026.05.28 14:05:00 | 1051 | 100.0 | 53.92 | 27.44 | 118 | 118 | PENDING |
| 2026-05-28T14:11:28.057971+00:00 | 2026.05.28 14:10:00 | 1052 | 100.0 | 53.92 | 27.49 | 118 | 118 | PENDING |
| 2026-05-28T14:15:31.452820+00:00 | 2026.05.28 14:15:00 | 1053 | 100.0 | 53.92 | 27.56 | 118 | 118 | PENDING |
| 2026-05-28T14:16:29.342518+00:00 | 2026.05.28 14:15:00 | 1053 | 100.0 | 53.92 | 27.58 | 118 | 118 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 14 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-27T00:31:32.458153+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
