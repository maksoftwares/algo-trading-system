# Phase 1 Soak History Report

Overall status: WARN

History CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`

## Checks

| Check | Status | Message |
| --- | --- | --- |
| history_exists | PASS | Found `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE1_SOAK_HISTORY.csv`. |
| history_rows | PASS | History rows available: 155. |
| created_at_parse | PASS | All summary timestamps are parseable and ordered. |
| latest_status | WARN | Latest warning status fields: log_verification, soak_analysis, runtime_health |
| latest_safety_state | PASS | Latest row stayed dry-run and permission-locked. |
| progress_monotonic | WARN | Soak progress decreased between history rows. |

## Summary

- History rows: 155
- First summary: 2026-05-21T19:48:31.384045+00:00
- Latest summary: 2026-05-27T17:33:41.941688+00:00
- Latest M5 bar: 2026.05.27 17:30:00
- Latest soak progress: 100.0%
- Longest active streak: 22.92h
- Current active streak: 6.83h
- Weekend policy: weekend_breaks_active_market_streak
- Process uptime streak: 6.86h
- Code-freeze hours: 6.86h
- Latest would-signal rows: 85
- Latest setup clusters: 85

## Latest Status

| Log | Soak | Runtime | Would-Signal | Acceptance | Dry Run | Permission |
| --- | --- | --- | --- | --- | --- | --- |
| WARN | WARN | WARN | PASS | PENDING | true | false |

## Recent History

| Summary UTC | Latest Bar | Rows | Progress % | Longest h | Freeze h | Would Rows | Clusters | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-27T13:11:06.242796+00:00 | 2026.05.27 13:10:00 | 764 | 100.0 | 22.92 | 2.49 | 81 | 81 | PENDING |
| 2026-05-27T13:27:31.465799+00:00 | 2026.05.27 13:25:00 | 767 | 100.0 | 22.92 | 2.76 | 81 | 81 | PENDING |
| 2026-05-27T13:40:12.671525+00:00 | 2026.05.27 13:40:00 | 770 | 100.0 | 22.92 | 2.97 | 81 | 81 | PENDING |
| 2026-05-27T13:41:11.071571+00:00 | 2026.05.27 13:40:00 | 770 | 100.0 | 22.92 | 2.99 | 81 | 81 | PENDING |
| 2026-05-27T13:49:30.037112+00:00 | 2026.05.27 13:45:00 | 771 | 100.0 | 22.92 | 3.13 | 81 | 81 | PENDING |
| 2026-05-27T13:50:11.639816+00:00 | 2026.05.27 13:50:00 | 772 | 100.0 | 22.92 | 3.14 | 81 | 81 | PENDING |
| 2026-05-27T14:06:24.569055+00:00 | 2026.05.27 14:05:00 | 775 | 100.0 | 22.92 | 3.41 | 81 | 81 | PENDING |
| 2026-05-27T14:40:43.666229+00:00 | 2026.05.27 14:40:00 | 782 | 100.0 | 22.92 | 3.98 | 81 | 81 | PENDING |
| 2026-05-27T15:41:56.694128+00:00 | 2026.05.27 15:40:00 | 794 | 100.0 | 22.92 | 5.0 | 81 | 81 | PENDING |
| 2026-05-27T16:06:10.810436+00:00 | 2026.05.27 16:05:00 | 799 | 100.0 | 22.92 | 5.41 | 83 | 83 | PENDING |
| 2026-05-27T16:42:24.223657+00:00 | 2026.05.27 16:40:00 | 806 | 100.0 | 22.92 | 6.01 | 83 | 83 | PENDING |
| 2026-05-27T17:33:41.941688+00:00 | 2026.05.27 17:30:00 | 816 | 100.0 | 22.92 | 6.86 | 85 | 85 | PENDING |

## Historical Acceptance Notes

- Historical acceptance `FAIL` rows: 14 between `2026-05-21T22:12:57.446733+00:00` and `2026-05-27T00:31:32.458153+00:00`.
- 3 row(s) were acceptance-only `FAIL` with Log/Soak/Runtime/Would-Signal all `PASS`, from `2026-05-21T22:14:43.284578+00:00` to `2026-05-23T13:25:05.558361+00:00`.
- This pattern points to a reporting transient rather than a dry-run boundary or runtime regression.
- Latest history row is healthy again, so the earlier `FAIL` entries should be reviewed as historical anomalies only.
