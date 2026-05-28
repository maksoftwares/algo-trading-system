# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 163. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | PASS | Latest status is healthy; acceptance is PENDING. |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 163
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-28T13:21:43.587117+00:00
- Latest M5 bar: 2026.05.28 13:20:00
- Latest soak progress: 100.0%
- Longest active streak: 53.92h
- Current active streak: 25.58h
- Weekend policy: expected_market_breaks_pause_active_market_streak
- Process uptime streak: 26.66h
- Code-freeze hours: 26.66h
- Latest would-signal rows: 118
- Latest setup clusters: 118

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-27T15:41:56.694128+00:00 | 2026.05.27 15:40:00 | 794 | 100.0 | 22.92 | 5.0 | 81 | 81 | PENDING |
| 2026-05-27T16:06:10.810436+00:00 | 2026.05.27 16:05:00 | 799 | 100.0 | 22.92 | 5.41 | 83 | 83 | PENDING |
| 2026-05-27T16:42:24.223657+00:00 | 2026.05.27 16:40:00 | 806 | 100.0 | 22.92 | 6.01 | 83 | 83 | PENDING |
| 2026-05-27T17:33:41.941688+00:00 | 2026.05.27 17:30:00 | 816 | 100.0 | 22.92 | 6.86 | 85 | 85 | PENDING |
| 2026-05-27T18:13:06.914764+00:00 | 2026.05.27 18:10:00 | 824 | 100.0 | 22.92 | 7.52 | 89 | 89 | PENDING |
| 2026-05-27T18:13:58.304506+00:00 | 2026.05.27 18:10:00 | 824 | 100.0 | 22.92 | 7.54 | 89 | 89 | PENDING |
| 2026-05-27T18:38:29.312886+00:00 | 2026.05.27 18:35:00 | 829 | 100.0 | 53.92 | 7.94 | 89 | 89 | PENDING |
| 2026-05-27T19:22:15.977027+00:00 | 2026.05.27 19:20:00 | 838 | 100.0 | 53.92 | 8.67 | 89 | 89 | PENDING |
| 2026-05-27T22:05:09.611187+00:00 | 2026.05.27 22:05:00 | 859 | 100.0 | 53.92 | 11.39 | 91 | 91 | PENDING |
| 2026-05-28T11:28:43.614183+00:00 | 2026.05.28 11:25:00 | 1019 | 100.0 | 53.92 | 24.78 | 110 | 110 | PENDING |
| 2026-05-28T13:14:10.199338+00:00 | 2026.05.28 13:10:00 | 1040 | 100.0 | 53.92 | 26.54 | 118 | 118 | PENDING |
| 2026-05-28T13:21:43.587117+00:00 | 2026.05.28 13:20:00 | 1042 | 100.0 | 53.92 | 26.66 | 118 | 118 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 14 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-27T00:31:32.458153+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
