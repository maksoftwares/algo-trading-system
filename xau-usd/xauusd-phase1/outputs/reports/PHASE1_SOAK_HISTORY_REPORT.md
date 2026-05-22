# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 45. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | WARN | Latest warning status fields: log_verification, runtime_health, would_signal |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 45
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-22T11:10:17.621338+00:00
- Latest M5 bar: 2026.05.22 11:10:00
- Latest soak progress: 0.14%
- Latest would-signal rows: 0
- Latest setup clusters: 0

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| WARN | PASS | WARN | WARN | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-05-22T06:41:56.603607+00:00 | 2026.05.22 06:40:00 | 197 | 14.1 | 14 | 14 | PENDING |
| 2026-05-22T07:01:07.365628+00:00 | 2026.05.22 07:00:00 | 201 | 14.37 | 14 | 14 | PENDING |
| 2026-05-22T07:12:15.307285+00:00 | 2026.05.22 07:10:00 | 203 | 14.51 | 14 | 14 | PENDING |
| 2026-05-22T08:01:11.937654+00:00 | 2026.05.22 08:00:00 | 213 | 15.21 | 14 | 14 | PENDING |
| 2026-05-22T09:03:52.537786+00:00 | 2026.05.22 09:00:00 | 225 | 16.04 | 14 | 14 | PENDING |
| 2026-05-22T09:04:05.336045+00:00 | 2026.05.22 09:00:00 | 225 | 16.04 | 14 | 14 | PENDING |
| 2026-05-22T10:04:38.804373+00:00 | 2026.05.22 10:00:00 | 237 | 16.88 | 14 | 14 | PENDING |
| 2026-05-22T11:06:06.926980+00:00 | 2026.05.22 11:05:00 | 3 | 0.07 | 0 | 0 | PENDING |
| 2026-05-22T11:06:33.057268+00:00 | 2026.05.22 11:05:00 | 3 | 0.07 | 0 | 0 | FAIL |
| 2026-05-22T11:08:17.659899+00:00 | 2026.05.22 11:05:00 | 3 | 0.07 | 0 | 0 | FAIL |
| 2026-05-22T11:09:54.942578+00:00 | 2026.05.22 11:05:00 | 3 | 0.07 | 0 | 0 | PENDING |
| 2026-05-22T11:10:17.621338+00:00 | 2026.05.22 11:10:00 | 4 | 0.14 | 0 | 0 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 5 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-22T11:08:17.659899+00:00`.
- 2 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-21T22:15:12.406592+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
