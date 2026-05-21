# Passive Bar Exporter

`PassiveBarExporter_Phase0.mq5` exports historical MT5 bars to CSV files for Phase 0 data acquisition. It is a script, not an expert with trade actions. It reads chart history and writes files only.

## Inputs

```text
InpSymbol=
InpBrokerLabel=capital_com
InpTimeframes=M5,M15,H1,H4,D1
InpStartServerTime=2016.01.01 00:00
InpEndServerTime=2025.06.30 23:59
InpServerToUtcOffsetHours=0
InpUseCommonFiles=true
InpPrintToExpertsTab=true
```

`InpStartServerTime` and `InpEndServerTime` are MT5 server-time values used to request history. The exporter writes UTC-adjusted timestamps by subtracting `InpServerToUtcOffsetHours`.

For brokers whose server offset changes during daylight saving periods, prefer broker portal exports with UTC timestamps, or export separate date ranges with the correct fixed offset for each range.

Use `bar_exporter_set_example.set` as a starting preset and adjust the symbol, broker label, date window, and offset before running the script.

## Output

The exporter writes files named:

```text
{symbol}_{timeframe}_{YYYYMMDD}_{YYYYMMDD}_{broker_label}.csv
```

Expected columns:

```text
<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<TICKVOL>,<SPREAD>
```

Copy completed CSV files from the MT5 Files folder into the matching repository folder:

```text
data/raw/{broker}/
```

Then run:

```powershell
python -m phase0 import-required-bars --fail-on-missing
python -m phase0 check-data-availability
```
