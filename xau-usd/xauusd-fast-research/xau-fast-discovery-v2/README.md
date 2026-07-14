# XAUUSD Fast Discovery V2

Bounded development-first research over six frozen XAUUSD strategy families. Signals use completed Mid bars; execution uses official Dukascopy native Bid/Ask ticks. There is no optimizer, EA, MT5 Strategy Tester, broker action, or deployment path in this lane.

Set the external bulk-data root and run Stage A:

```powershell
$env:DUKASCOPY_TICK_DATA_ROOT = '<external-root>'
python run_discovery.py stage-a --concurrency 4
```

Stage B is not acquired unless a frozen family passes every development gate.
