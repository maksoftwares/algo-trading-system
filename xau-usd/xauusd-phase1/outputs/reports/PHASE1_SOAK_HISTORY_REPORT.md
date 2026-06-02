# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 257. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | PASS | Latest status is healthy; acceptance is PASS. |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 257
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-06-02T14:08:43.979663+00:00
- Latest M5 bar: 2026.06.02 14:05:00
- Latest soak progress: 100.0%
- Longest active streak: 56.08h
- Current active streak: 37.0h
- Weekend policy: expected_market_breaks_pause_active_market_streak
- Process uptime streak: 38.85h
- Code-freeze hours: 147.45h
- Latest would-signal rows: 203
- Latest setup clusters: 203

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PASS | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-31T23:32:24.477529+00:00 | 2026.05.31 23:30:00 | 1413 | 100.0 | 56.08 | 108.84 | 161 | 161 | PENDING |
| 2026-06-01T05:30:58.140414+00:00 | 2026.06.01 05:30:00 | 1485 | 100.0 | 56.08 | 114.82 | 168 | 168 | PENDING |
| 2026-06-01T05:39:20.091056+00:00 | 2026.06.01 05:35:00 | 1486 | 100.0 | 56.08 | 114.96 | 168 | 168 | PENDING |
| 2026-06-01T05:40:29.222566+00:00 | 2026.06.01 05:40:00 | 1487 | 100.0 | 56.08 | 114.98 | 168 | 168 | PASS |
| 2026-06-01T06:35:17.231392+00:00 | 2026.06.01 06:35:00 | 1498 | 100.0 | 56.08 | 115.89 | 171 | 171 | PASS |
| 2026-06-01T06:36:21.796173+00:00 | 2026.06.01 06:35:00 | 1498 | 100.0 | 56.08 | 115.91 | 171 | 171 | PASS |
| 2026-06-01T06:46:29.321108+00:00 | 2026.06.01 06:45:00 | 1500 | 100.0 | 56.08 | 116.08 | 173 | 173 | PASS |
| 2026-06-02T06:53:33.294466+00:00 | 2026.06.02 06:50:00 | 1777 | 100.0 | 56.08 | 140.2 | 197 | 197 | PASS |
| 2026-06-02T08:13:17.132662+00:00 | 2026.06.02 08:10:00 | 1793 | 100.0 | 56.08 | 141.52 | 199 | 199 | PASS |
| 2026-06-02T10:24:40.393341+00:00 | 2026.06.02 10:20:00 | 1819 | 100.0 | 56.08 | 143.71 | 201 | 201 | PASS |
| 2026-06-02T13:57:30.792719+00:00 | 2026.06.02 13:55:00 | 1862 | 100.0 | 56.08 | 147.26 | 203 | 203 | PASS |
| 2026-06-02T14:08:43.979663+00:00 | 2026.06.02 14:05:00 | 1864 | 100.0 | 56.08 | 147.45 | 203 | 203 | PASS |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 14 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-27T00:31:32.458153+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
