# Dukascopy Macro Prospective Snapshot V1

Resumable, data-only acquisition of completed `DOLLARIDXUSD` and
`USTBONDTRUSD` tick hours after the July 1 research cutoff. It uses the free
official Dukascopy endpoint, caps concurrency at four, and never requests the
open UTC hour.

The M5 builder must reproduce the frozen June 30 macro cache before it writes
prospective features. No paid source, strategy scoring, account, or broker
action is authorized.

```powershell
$env:DUKASCOPY_TICK_DATA_ROOT = 'D:\AlgoTradingData\C_DRIVE\DukascopyTickDataFoundationV1'
python acquire_snapshot.py --end-exclusive 2026-07-22T15:00:00Z
python verify_snapshot.py '<snapshot-manifest>'
python build_m5_snapshot.py '<snapshot-manifest>'
```

`run_continuous.py` resumes the archive to the latest completed UTC hour,
rebuilds the same parity-checked M5 feature cache only when the endpoint
advances, and publishes a data-only health file for the runtime supervisor.
Closed-market hours are retained as valid zero-tick source hours.

```powershell
python run_continuous.py --watch --poll-seconds 900
```
