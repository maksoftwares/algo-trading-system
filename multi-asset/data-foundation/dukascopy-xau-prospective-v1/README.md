# Dukascopy XAU Prospective Snapshot V1

Resumable acquisition of completed XAUUSD bid/ask tick hours after the frozen
`2026-07-01` research cutoff. It reuses the checksum-pinned official Dukascopy
foundation downloader, never requests the open UTC hour, and writes a snapshot
manifest outside Git.

It uses no Databento service or paid data source and contains no strategy, P/L,
account, or broker action.

```powershell
$env:DUKASCOPY_TICK_DATA_ROOT = 'D:\AlgoTradingData\C_DRIVE\DukascopyTickDataFoundationV1'
python acquire_snapshot.py --end-exclusive 2026-07-22T15:00:00Z
python verify_snapshot.py '<snapshot-manifest-path>'
python build_m5_snapshot.py '<snapshot-manifest-path>' '<frozen-m5-cache-path>'
```
