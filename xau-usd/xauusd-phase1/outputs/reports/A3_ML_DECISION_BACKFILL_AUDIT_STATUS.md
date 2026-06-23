# A3 ML Decision Backfill Audit

Overall status: CURRENT_SCOPE_EXHAUSTED_OUT_OF_SCOPE_BACKFILL_FOUND
Dataset version: xauusd_c02_multiacct_202606220547_geffebb6d_c9221d066

## Summary

- Signal-like CSV files scanned: 113
- Current-scope would-signal rows: 574
- Uncataloged current-scope files: 0
- Out-of-scope would-signal rows: 2747
- Out-of-scope estimated groups: 1381

## Family Summary

| Family | Rows | Groups | Files | Min | Max |
| --- | --- | --- | --- | --- | --- |
| rdguard | 78 | 78 | 1 | 2026-06-14T22:39:59Z | 2026-06-16T11:14:56Z |
| rdstruct | 78 | 78 | 1 | 2026-06-14T22:39:59Z | 2026-06-16T11:14:56Z |
| round_number_retest | 2455 | 1127 | 7 | 2026-05-29T09:34:56Z | 2026-06-19T16:10:00Z |
| session_extreme_retest | 136 | 98 | 4 | 2026-05-29T13:05:00Z | 2026-06-19T16:14:59Z |

## Uncataloged Current Scope

No uncataloged current-scope files found.

## Out-Of-Scope Candidates

| Account | File | Family | Rows | Min | Max |
| --- | --- | --- | --- | --- | --- |
| A1 | experimental_demo_attachment_log_round_number_retest_v0_xauusd.csv | round_number_retest | 56 | 2026-05-29T09:34:56Z | 2026-06-01T10:59:58Z |
| A1 | experimental_demo_attachment_log_session_extreme_retest_v0_xauusd.csv | session_extreme_retest | 7 | 2026-05-29T13:05:00Z | 2026-06-01T10:59:58Z |
| A1 | experimental_demo_attachment_log_symbol_normalized_round_retest_v0_xauusd.csv | round_number_retest | 56 | 2026-05-29T09:34:56Z | 2026-06-01T10:59:58Z |
| A1 | experimental_demo_executor_signal_log_round_number_retest_v0_xauusd.csv | round_number_retest | 353 | 2026-06-01T11:09:58Z | 2026-06-08T12:24:56Z |
| A1 | experimental_demo_executor_signal_log_session_extreme_retest_v0_xauusd.csv | session_extreme_retest | 37 | 2026-06-01T11:54:58Z | 2026-06-04T22:24:59Z |
| A1 | experimental_demo_executor_signal_log_symbol_normalized_round_retest_v0_xauusd.csv | round_number_retest | 353 | 2026-06-01T11:09:58Z | 2026-06-08T12:24:56Z |
| A1 | experimental_demo_executor_signal_log_v02_round_number_retest_v0_xauusd.csv | round_number_retest | 517 | 2026-06-08T13:09:56Z | 2026-06-17T10:49:56Z |
| A1 | experimental_demo_executor_signal_log_v02_session_extreme_retest_v0_xauusd.csv | session_extreme_retest | 49 | 2026-06-08T14:20:00Z | 2026-06-18T15:14:59Z |
| A1 | experimental_demo_executor_signal_log_v02_symbol_normalized_round_retest_v0_xauusd.csv | round_number_retest | 517 | 2026-06-08T13:09:56Z | 2026-06-17T10:49:56Z |
| A1 | phase2_demo_repair_executor_signal_log_v1_session_extreme_retest_v0_repair_v1_xauusd.csv | session_extreme_retest | 43 | 2026-06-09T14:35:00Z | 2026-06-19T16:14:59Z |
| A1 | phase2_demo_repair_executor_signal_log_v1_symbol_normalized_round_retest_v0_repair_v1_xauusd.csv | round_number_retest | 603 | 2026-06-09T08:14:56Z | 2026-06-19T16:10:00Z |
| A3 | a3_rdguard_v1_signal_log.csv | rdguard | 78 | 2026-06-14T22:39:59Z | 2026-06-16T11:14:56Z |
| A3 | a3_rdstruct_v1_signal_log.csv | rdstruct | 78 | 2026-06-14T22:39:59Z | 2026-06-16T11:14:56Z |

## Boundary

- MT5 connection attempted: false.
- Data export attempted: false.
- Terminal runtime change authorized: false.
- Model training authorized: false.
- Python demo predictions authorized: false.
- Broker action authorized: false.

## Next

Do not import out-of-scope rows into the locked model. Ask reviewer to approve or reject a multi-family C02/C03 contract expansion.
