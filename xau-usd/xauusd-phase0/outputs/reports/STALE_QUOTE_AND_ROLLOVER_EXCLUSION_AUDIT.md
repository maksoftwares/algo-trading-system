# Stale Quote And Rollover Exclusion Audit

Overall status: PASS
Generated at UTC: 2026-06-02T11:44:05Z

| Check | Status | Evidence |
| --- | --- | --- |
| Freshness and closed-market filtering | PASS | tick_fresh_reported=True; weekend_buckets_present=False |
| Authoritative global measured model | PASS | symbol=XAUUSD; global_row_present=True; p95=75.0 |
| Rollover diagnostic retained separately | PASS | rollover_rows=1; rollover rows are diagnostic, not a same-family rescue filter. |
| Weekend exclusion | PASS | day_of_week_buckets=['Friday', 'Monday', 'Thursday', 'Tuesday', 'Wednesday'] |

Rollover and hour-of-day diagnostics may explain damage, but they must not be used to patch `breakout_retest_v1.0` after failure.
