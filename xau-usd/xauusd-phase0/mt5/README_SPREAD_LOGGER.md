# Passive Spread Logger

`PassiveSpreadLogger_XAUUSD.mq5` collects broker spread observations for Phase 0 cost calibration. It writes CSV rows on a timer and updates a chart dashboard.

It is a logger only. It must not include live order placement, order modification, position management, or any trading library include.

## Inputs

```text
InpSymbol=
InpLogIntervalSeconds=5
InpUseCommonFiles=false
InpFilePrefix=spread_log
InpPrintToExpertsTab=false
InpRolloverHourServer=22
InpRolloverWindowMinutes=30
InpMaxTickAgeSeconds=30
```

## Output

The logger writes files named:

```text
spread_log_{account}_{server}_{symbol}_{YYYYMMDD}.csv
```

Expected columns:

```text
broker_time,gmt_time,local_time,tick_time,tick_time_msc,seconds_since_tick,tick_fresh,account,server,symbol,bid,ask,spread_price,spread_points,point,digits,session_label,is_rollover_window
```

The analyzer only admits rows where `tick_fresh=true`, so stale quotes cannot silently contaminate the measured-cost model.

The recommended Phase 1/Phase 2 prep setting is `InpUseCommonFiles=false`, which writes into the active MT5 Portable `MQL5/Files` directory. Then run:

```powershell
.\.venv\Scripts\phase0.exe generate-measured-cost-model --input-dir C:\MT5PortableGoldMission\MQL5\Files
.\.venv\Scripts\phase0.exe generate-measured-cost-revalidation --expert breakout_retest
```
