# Phase 1 Soak History Report

Overall status: PASS

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 34. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | PASS | Latest status is healthy; acceptance is PENDING. |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | PASS | Soak progress is monotonic. |

## Summary

- History rows: 34
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-22T06:41:56.603607+00:00
- Latest M5 bar: 2026.05.22 06:40:00
- Latest soak progress: 14.1%
- Latest would-signal rows: 14
- Latest setup clusters: 14

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-05-22T05:28:50.122794+00:00 | 2026.05.22 05:25:00 | 182 | 13.06 | 12 | 12 | PENDING |
| 2026-05-22T05:59:40.705227+00:00 | 2026.05.22 05:55:00 | 188 | 13.47 | 13 | 13 | PENDING |
| 2026-05-22T06:05:02.763056+00:00 | 2026.05.22 06:05:00 | 190 | 13.61 | 13 | 13 | PENDING |
| 2026-05-22T06:05:06.898675+00:00 | 2026.05.22 06:05:00 | 190 | 13.61 | 13 | 13 | PENDING |
| 2026-05-22T06:30:51.507653+00:00 | 2026.05.22 06:30:00 | 195 | 13.96 | 14 | 14 | PENDING |
| 2026-05-22T06:30:58.431574+00:00 | 2026.05.22 06:30:00 | 195 | 13.96 | 14 | 14 | PENDING |
| 2026-05-22T06:35:09.105521+00:00 | 2026.05.22 06:35:00 | 196 | 14.03 | 14 | 14 | PENDING |
| 2026-05-22T06:35:40.665351+00:00 | 2026.05.22 06:35:00 | 196 | 14.03 | 14 | 14 | PENDING |
| 2026-05-22T06:37:02.610178+00:00 | 2026.05.22 06:35:00 | 196 | 14.03 | 14 | 14 | PENDING |
| 2026-05-22T06:37:07.652332+00:00 | 2026.05.22 06:35:00 | 196 | 14.03 | 14 | 14 | PENDING |
| 2026-05-22T06:41:56.240237+00:00 | 2026.05.22 06:40:00 | 197 | 14.1 | 14 | 14 | PENDING |
| 2026-05-22T06:41:56.603607+00:00 | 2026.05.22 06:40:00 | 197 | 14.1 | 14 | 14 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 3 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-21T22:15:12.406592+00:00`.
- 2 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-21T22:15:12.406592+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
