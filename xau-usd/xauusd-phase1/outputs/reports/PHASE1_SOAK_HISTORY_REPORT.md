# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 239. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | PASS | Latest status is healthy; acceptance is PENDING. |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 239
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-29T11:39:20.180870+00:00
- Latest M5 bar: 2026.05.29 11:35:00
- Latest soak progress: 100.0%
- Longest active streak: 53.92h
- Current active streak: 46.75h
- Weekend policy: expected_market_breaks_pause_active_market_streak
- Process uptime streak: 48.96h
- Code-freeze hours: 48.96h
- Latest would-signal rows: 148
- Latest setup clusters: 148

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-28T18:08:34.897383+00:00 | 2026.05.28 18:05:00 | 1099 | 100.0 | 53.92 | 31.45 | 118 | 118 | PENDING |
| 2026-05-28T18:13:37.880026+00:00 | 2026.05.28 18:10:00 | 1100 | 100.0 | 53.92 | 31.53 | 118 | 118 | PENDING |
| 2026-05-28T18:19:51.879919+00:00 | 2026.05.28 18:15:00 | 1101 | 100.0 | 53.92 | 31.63 | 118 | 118 | PENDING |
| 2026-05-28T18:26:24.905678+00:00 | 2026.05.28 18:25:00 | 1103 | 100.0 | 53.92 | 31.74 | 118 | 118 | PENDING |
| 2026-05-28T18:27:58.516383+00:00 | 2026.05.28 18:25:00 | 1103 | 100.0 | 53.92 | 31.77 | 118 | 118 | PENDING |
| 2026-05-28T18:33:46.705230+00:00 | 2026.05.28 18:30:00 | 1104 | 100.0 | 53.92 | 31.87 | 118 | 118 | PENDING |
| 2026-05-28T18:37:43.696340+00:00 | 2026.05.28 18:35:00 | 1105 | 100.0 | 53.92 | 31.93 | 118 | 118 | PENDING |
| 2026-05-28T18:40:25.421316+00:00 | 2026.05.28 18:40:00 | 1106 | 100.0 | 53.92 | 31.98 | 118 | 118 | PENDING |
| 2026-05-28T18:43:20.144609+00:00 | 2026.05.28 18:40:00 | 1106 | 100.0 | 53.92 | 32.03 | 118 | 118 | PENDING |
| 2026-05-28T18:46:29.608433+00:00 | 2026.05.28 18:45:00 | 1107 | 100.0 | 53.92 | 32.08 | 118 | 118 | PENDING |
| 2026-05-28T19:34:45.657728+00:00 | 2026.05.28 19:30:00 | 1116 | 100.0 | 53.92 | 32.88 | 118 | 118 | PENDING |
| 2026-05-29T11:39:20.180870+00:00 | 2026.05.29 11:35:00 | 1297 | 100.0 | 53.92 | 48.96 | 148 | 148 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 14 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-27T00:31:32.458153+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
