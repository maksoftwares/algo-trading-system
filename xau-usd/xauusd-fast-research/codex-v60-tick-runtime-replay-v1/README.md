# V60 Tick Runtime Replay V1

Read-only reproduction of the deployed V60 risk state machine on historical
Dukascopy bid/ask ticks, with an optional reproduction of the attached MT5
daily guardian.

Run with the repository's research Python environment:

```powershell
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe run_replay.py
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe -m pytest -q
```

The first run prepares a memory-mapped 5-second quote cache on the D drive.
Research outputs remain in `outputs/`. The script never imports MetaTrader5
and never writes to terminal or account directories.
