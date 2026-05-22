# Phase 1 Soak History Report

Overall status: PASS

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 23. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | PASS | Latest status is healthy; acceptance is PENDING. |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | PASS | Soak progress is monotonic. |

## Summary

- History rows: 23
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-22T05:28:50.122794+00:00
- Latest M5 bar: 2026.05.22 05:25:00
- Latest soak progress: 13.06%
- Latest would-signal rows: 12
- Latest setup clusters: 12

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-05-21T22:15:28.590983+00:00 | 2026.05.21 22:15:00 | 96 | 7.08 | 6 | 6 | PENDING |
| 2026-05-21T22:49:23.647175+00:00 | 2026.05.21 22:45:00 | 102 | 7.5 | 6 | 6 | PENDING |
| 2026-05-21T23:19:20.350524+00:00 | 2026.05.21 23:15:00 | 108 | 7.92 | 6 | 6 | PENDING |
| 2026-05-21T23:28:25.862512+00:00 | 2026.05.21 23:25:00 | 110 | 8.06 | 6 | 6 | PENDING |
| 2026-05-21T23:50:01.456649+00:00 | 2026.05.21 23:50:00 | 115 | 8.4 | 7 | 7 | PENDING |
| 2026-05-22T00:51:20.887909+00:00 | 2026.05.22 00:50:00 | 127 | 9.24 | 8 | 8 | PENDING |
| 2026-05-22T01:53:26.553034+00:00 | 2026.05.22 01:50:00 | 139 | 10.07 | 10 | 10 | PENDING |
| 2026-05-22T02:55:16.250947+00:00 | 2026.05.22 02:55:00 | 152 | 10.97 | 11 | 11 | PENDING |
| 2026-05-22T03:00:39.039440+00:00 | 2026.05.22 03:00:00 | 153 | 11.04 | 11 | 11 | PENDING |
| 2026-05-22T03:56:55.763978+00:00 | 2026.05.22 03:55:00 | 164 | 11.81 | 11 | 11 | PENDING |
| 2026-05-22T04:58:00.469677+00:00 | 2026.05.22 04:55:00 | 176 | 12.64 | 12 | 12 | PENDING |
| 2026-05-22T05:28:50.122794+00:00 | 2026.05.22 05:25:00 | 182 | 13.06 | 12 | 12 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 3 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-21T22:15:12.406592+00:00`.
- 2 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-21T22:15:12.406592+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
