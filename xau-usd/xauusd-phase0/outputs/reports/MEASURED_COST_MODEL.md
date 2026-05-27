# Measured Cost Model

Overall status: PENDING

## Decision

Measured spread evidence is not sufficient yet. Keep Phase 2 readiness pending.

## Coverage

| Observed Rows | Required Rows | Observed Days | Required Days | Source Rows | Rows Missing Tick Fresh | Weekend Rows Excluded | Tick Freshness | Source Files |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6624 | 500 | 1 | 5 | 62328 | 55704 | 0 | available | 6 |

## Global Cost Model

| scope | bucket | broker | symbol | observations | median_spread_points | p95_spread_points | max_spread_points |
| --- | --- | --- | --- | --- | --- | --- | --- |
| global | all | all | XAUUSD | 6624 | 50 | 75 | 75 |

## Source Files

- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260522.csv
- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260523.csv
- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260524.csv
- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260525.csv
- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260526.csv
- C:\MT5PortableSpreadLogger\MQL5\Files\spread_log_121409_Capital.ComMena-Live_XAUUSD_20260527.csv

## Note

Measured cost model generated from passive spread logger data after filtering to tick_fresh=true rows. Rows excluded because tick_fresh was not true or was missing: 55704; rows missing tick_fresh: 55704. Weekend/closed-market rows excluded: 0. Missing freshness columns: none.

Missing freshness columns: none
