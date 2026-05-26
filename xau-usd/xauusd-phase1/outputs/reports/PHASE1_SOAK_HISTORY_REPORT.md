# Phase 1 Soak History Report

Overall status: FAIL

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 115. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | FAIL | Latest failing status fields: log_verification |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 115
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-26T21:21:41.962701+00:00
- Latest M5 bar: 2026.05.26 20:55:00
- Latest soak progress: 88.26%
- Longest active streak: 22.92h
- Current active streak: 22.92h
- Weekend policy: weekend_breaks_active_market_streak
- Process uptime streak: 106.3h
- Code-freeze hours: 59.74h
- Latest would-signal rows: 61
- Latest setup clusters: 61

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| FAIL | WARN | WARN | PASS | FAIL | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-26T01:59:49.954527+00:00 | 2026.05.26 01:55:00 | 350 | 72.43 | 18.33 | 40.37 | 31 | 31 | PENDING |
| 2026-05-26T03:18:09.914625+00:00 | 2026.05.26 03:15:00 | 366 | 73.54 | 18.33 | 41.68 | 31 | 31 | PENDING |
| 2026-05-26T04:02:19.811278+00:00 | 2026.05.26 04:00:00 | 375 | 74.17 | 18.33 | 42.41 | 31 | 31 | PENDING |
| 2026-05-26T05:04:20.772416+00:00 | 2026.05.26 05:00:00 | 387 | 75.0 | 18.33 | 43.45 | 31 | 31 | PENDING |
| 2026-05-26T06:19:58.599802+00:00 | 2026.05.26 06:20:00 | 403 | 76.11 | 18.33 | 44.71 | 33 | 33 | PENDING |
| 2026-05-26T07:08:00.678344+00:00 | 2026.05.26 07:05:00 | 412 | 76.74 | 18.33 | 45.51 | 33 | 33 | PENDING |
| 2026-05-26T08:27:37.145368+00:00 | 2026.05.26 08:25:00 | 428 | 77.85 | 18.33 | 46.83 | 35 | 35 | PENDING |
| 2026-05-26T12:18:57.083403+00:00 | 2026.05.26 12:15:00 | 474 | 81.04 | 18.33 | 50.69 | 41 | 41 | PENDING |
| 2026-05-26T13:19:14.910582+00:00 | 2026.05.26 13:15:00 | 486 | 81.88 | 18.33 | 51.7 | 43 | 43 | PENDING |
| 2026-05-26T14:21:28.473976+00:00 | 2026.05.26 14:20:00 | 499 | 82.78 | 18.33 | 52.73 | 47 | 47 | PENDING |
| 2026-05-26T20:24:04.331967+00:00 | 2026.05.26 20:20:00 | 571 | 87.78 | 22.33 | 58.78 | 61 | 61 | PENDING |
| 2026-05-26T21:21:41.962701+00:00 | 2026.05.26 20:55:00 | 578 | 88.26 | 22.92 | 59.74 | 61 | 61 | FAIL |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 8 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-26T21:21:41.962701+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
