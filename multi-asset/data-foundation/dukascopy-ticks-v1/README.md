# Dukascopy Multi-Asset Bid/Ask Tick Data Foundation V1

This lane acquires and validates official Dukascopy hourly bid/ask tick responses, preserves raw bytes outside Git, normalizes ticks to deterministic Zstd Parquet, and derives UTC-aligned Bid/Ask/Mid bars.

It is data infrastructure only. It contains no signal, trade, P/L, account, leverage, or deployment logic.

Set `DUKASCOPY_TICK_DATA_ROOT` to an external storage directory before running. The runner fails closed when it is absent or points inside this lane.

```powershell
$env:DUKASCOPY_TICK_DATA_ROOT = '<external-storage-root>'
python run_foundation.py --month 2016-07
```

Use `--all-months` only after the storage preflight passes. Acquisition uses no more than four concurrent requests and retries a missing or corrupt response exactly once.
