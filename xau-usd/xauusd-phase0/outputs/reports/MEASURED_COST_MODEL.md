# Measured Cost Model

Overall status: PENDING

## Decision

Measured spread evidence is not sufficient yet. Keep Phase 2 readiness pending.

## Coverage

| Observed Rows | Required Rows | Observed Days | Required Days | Source Rows | Rows Missing Tick Fresh | Weekend Rows Excluded | Tick Freshness | Source Files |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 26341 | 500 | 2 | 5 | 82705 | 55704 | 0 | available | 7 |

## Global Cost Model

| scope | bucket | broker | symbol | observations | median_spread_points | p95_spread_points | max_spread_points |
| --- | --- | --- | --- | --- | --- | --- | --- |
| global | all | all | XAUUSD | 26341 | 50 | 75 | 180 |

## Fresh Observed Dates

- 2026-05-27
- 2026-05-28

## Source Files

- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260522.csv
- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260523.csv
- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260524.csv
- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260525.csv
- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260526.csv
- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260527.csv
- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260528.csv

## Note

Measured cost model generated from passive spread logger data after filtering to tick_fresh=true rows. Rows excluded because tick_fresh was not true or was missing: 56364; rows missing tick_fresh: 55704. Weekend/closed-market rows excluded: 0. Missing freshness columns: none.

## Why Observed Days Reset

Legacy spread logs before the freshness-aware logger redeployment did not include `tick_fresh` / `seconds_since_tick`, so they are retained as diagnostic source files but excluded from authoritative measured-cost gating. Fresh observed market days, not source-file count or legacy row count, control PASS/PENDING.

Missing freshness columns: none
