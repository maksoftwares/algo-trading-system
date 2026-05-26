# Spread Log Freshness Schema Warning

Overall status: WARN

The passive spread analyzer requires tick freshness columns. Existing legacy spread logs were left untouched so the Phase 1 periodic checks can continue using the last generated measured-cost evidence.

Reason: Spread log C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260522.csv missing column(s): tick_time, tick_time_msc, seconds_since_tick, tick_fresh.
