# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 190. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | PASS | Latest status is healthy; acceptance is PENDING. |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 190
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-28T15:13:03.933439+00:00
- Latest M5 bar: 2026.05.28 15:10:00
- Latest soak progress: 100.0%
- Longest active streak: 53.92h
- Current active streak: 27.42h
- Weekend policy: expected_market_breaks_pause_active_market_streak
- Process uptime streak: 28.52h
- Code-freeze hours: 28.52h
- Latest would-signal rows: 118
- Latest setup clusters: 118

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-28T14:25:41.659939+00:00 | 2026.05.28 14:25:00 | 1055 | 100.0 | 53.92 | 27.73 | 118 | 118 | PENDING |
| 2026-05-28T14:29:55.658668+00:00 | 2026.05.28 14:25:00 | 1055 | 100.0 | 53.92 | 27.8 | 118 | 118 | PENDING |
| 2026-05-28T14:32:26.619190+00:00 | 2026.05.28 14:30:00 | 1056 | 100.0 | 53.92 | 27.84 | 118 | 118 | PENDING |
| 2026-05-28T14:36:35.237154+00:00 | 2026.05.28 14:35:00 | 1057 | 100.0 | 53.92 | 27.91 | 118 | 118 | PENDING |
| 2026-05-28T14:44:36.906823+00:00 | 2026.05.28 14:40:00 | 1058 | 100.0 | 53.92 | 28.05 | 118 | 118 | PENDING |
| 2026-05-28T14:46:35.280663+00:00 | 2026.05.28 14:45:00 | 1059 | 100.0 | 53.92 | 28.08 | 118 | 118 | PENDING |
| 2026-05-28T14:47:12.972707+00:00 | 2026.05.28 14:45:00 | 1059 | 100.0 | 53.92 | 28.09 | 118 | 118 | PENDING |
| 2026-05-28T14:51:37.425962+00:00 | 2026.05.28 14:50:00 | 1060 | 100.0 | 53.92 | 28.16 | 118 | 118 | PENDING |
| 2026-05-28T14:54:59.130807+00:00 | 2026.05.28 14:50:00 | 1060 | 100.0 | 53.92 | 28.22 | 118 | 118 | PENDING |
| 2026-05-28T15:03:43.328370+00:00 | 2026.05.28 15:00:00 | 1062 | 100.0 | 53.92 | 28.36 | 118 | 118 | PENDING |
| 2026-05-28T15:09:59.031965+00:00 | 2026.05.28 15:05:00 | 1063 | 100.0 | 53.92 | 28.47 | 118 | 118 | PENDING |
| 2026-05-28T15:13:03.933439+00:00 | 2026.05.28 15:10:00 | 1064 | 100.0 | 53.92 | 28.52 | 118 | 118 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 14 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-27T00:31:32.458153+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
