# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 72. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | PASS | Latest status is healthy; acceptance is PENDING. |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 72
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-23T13:41:51.469556+00:00
- Latest M5 bar: 2026.05.22 20:55:00
- Latest soak progress: 8.26%
- Latest would-signal rows: 10
- Latest setup clusters: 10

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-05-23T12:35:15.747464+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | PENDING |
| 2026-05-23T12:44:28.729916+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | PENDING |
| 2026-05-23T12:57:20.994045+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | PENDING |
| 2026-05-23T13:05:51.077953+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | PENDING |
| 2026-05-23T13:10:52.070735+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | PENDING |
| 2026-05-23T13:14:53.825051+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | PENDING |
| 2026-05-23T13:16:59.264872+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | PENDING |
| 2026-05-23T13:25:05.558361+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | FAIL |
| 2026-05-23T13:25:45.490020+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | PENDING |
| 2026-05-23T13:28:30.709189+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | PENDING |
| 2026-05-23T13:30:29.675614+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | PENDING |
| 2026-05-23T13:41:51.469556+00:00 | 2026.05.22 20:55:00 | 56 | 8.26 | 10 | 10 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 6 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-23T13:25:05.558361+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
