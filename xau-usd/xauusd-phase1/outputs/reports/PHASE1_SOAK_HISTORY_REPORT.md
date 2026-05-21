# Phase 1 Soak History Report

Overall status: PASS

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 7. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | PASS | Latest status is healthy; acceptance is PENDING. |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | PASS | Soak progress is monotonic. |

## Summary

- History rows: 7
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-21T20:16:24.309384+00:00
- Latest M5 bar: 2026.05.21 20:15:00
- Latest soak progress: 5.42%
- Latest would-signal rows: 5
- Latest setup clusters: 5

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| PASS | PASS | PASS | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-05-21T19:48:31.384045+00:00 | 2026.05.21 19:45:00 | 78 | 5.0 | 4 | 4 | PENDING |
| 2026-05-21T19:55:41.861919+00:00 | 2026.05.21 19:55:00 | 80 | 5.14 | 4 | 4 | PENDING |
| 2026-05-21T19:56:40.945509+00:00 | 2026.05.21 19:55:00 | 80 | 5.14 | 4 | 4 | PENDING |
| 2026-05-21T19:59:58.629836+00:00 | 2026.05.21 19:55:00 | 80 | 5.14 | 4 | 4 | PENDING |
| 2026-05-21T20:01:47.627431+00:00 | 2026.05.21 20:00:00 | 81 | 5.21 | 4 | 4 | PENDING |
| 2026-05-21T20:09:33.123064+00:00 | 2026.05.21 20:05:00 | 82 | 5.28 | 4 | 4 | PENDING |
| 2026-05-21T20:16:24.309384+00:00 | 2026.05.21 20:15:00 | 84 | 5.42 | 5 | 5 | PENDING |
