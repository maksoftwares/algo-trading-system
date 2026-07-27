# V6 Causal ML Early Exit V3

This quarantined offline lane tests whether a post-entry classifier can reduce
losses and drawdown after the frozen V1 entry veto has selected a trade.

The classifier observes only completed bars at 30, 60, 120, and 240 minutes.
An early exit is filled at the following Capital.com M5 open. Entries, sizing,
the V60 core, and the frozen V1 entry model are not changed.

Historical success is not execution permission. The outputs cannot be consumed
by an EA, demo account, live account, or broker process.

Run:

```powershell
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe run_experiment.py
```

Test:

```powershell
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe -m pytest -q
```
