# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 249. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | PASS | Latest status is healthy; acceptance is PASS. |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 249
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-06-01T05:40:29.222566+00:00
- Latest M5 bar: 2026.06.01 05:40:00
- Latest soak progress: 100.0%
- Longest active streak: 56.08h
- Current active streak: 5.67h
- Weekend policy: expected_market_breaks_pause_active_market_streak
- Process uptime streak: 6.38h
- Code-freeze hours: 114.98h
- Latest would-signal rows: 168
- Latest setup clusters: 168

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PASS | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-28T19:34:45.657728+00:00 | 2026.05.28 19:30:00 | 1116 | 100.0 | 53.92 | 32.88 | 118 | 118 | PENDING |
| 2026-05-29T11:39:20.180870+00:00 | 2026.05.29 11:35:00 | 1297 | 100.0 | 53.92 | 48.96 | 148 | 148 | PENDING |
| 2026-05-30T21:03:57.610148+00:00 | 2026.05.29 20:55:00 | 1407 | 100.0 | 56.08 | 82.37 | 157 | 157 | PENDING |
| 2026-05-31T10:42:20.098152+00:00 | 2026.05.29 20:55:00 | 1407 | 100.0 | 56.08 | 96.01 | 157 | 157 | PENDING |
| 2026-05-31T23:14:56.525009+00:00 | 2026.05.31 23:10:00 | 1408 | 100.0 | 56.08 | 108.55 | 157 | 157 | PENDING |
| 2026-05-31T23:19:30.381562+00:00 | 2026.05.31 23:15:00 | 1410 | 100.0 | 56.08 | 108.63 | 157 | 157 | PENDING |
| 2026-05-31T23:26:55.487317+00:00 | 2026.05.31 23:25:00 | 1412 | 100.0 | 56.08 | 108.75 | 161 | 161 | PENDING |
| 2026-05-31T23:29:44.210907+00:00 | 2026.05.31 23:25:00 | 1412 | 100.0 | 56.08 | 108.8 | 161 | 161 | PENDING |
| 2026-05-31T23:32:24.477529+00:00 | 2026.05.31 23:30:00 | 1413 | 100.0 | 56.08 | 108.84 | 161 | 161 | PENDING |
| 2026-06-01T05:30:58.140414+00:00 | 2026.06.01 05:30:00 | 1485 | 100.0 | 56.08 | 114.82 | 168 | 168 | PENDING |
| 2026-06-01T05:39:20.091056+00:00 | 2026.06.01 05:35:00 | 1486 | 100.0 | 56.08 | 114.96 | 168 | 168 | PENDING |
| 2026-06-01T05:40:29.222566+00:00 | 2026.06.01 05:40:00 | 1487 | 100.0 | 56.08 | 114.98 | 168 | 168 | PASS |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 14 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-27T00:31:32.458153+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
