# V6 Causal ML Early Exit Utility V4

This offline lane responds to V3's main failure: a binary classifier correctly
identified many avoidable losses but a few premature exits sacrificed more
dollars than the correct exits saved.

V4 predicts the 25th percentile of the stressed benefit from exiting now rather
than holding the frozen trade. It exits only when that conservative predicted
benefit is positive and the completed path is materially adverse.

The V1 entry filter, V60 baseline, sizing, and execution permissions remain
unchanged. Historical success cannot authorize EA, demo, live, or broker use.

Run:

```powershell
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe run_experiment.py
```

Test:

```powershell
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe -m pytest -q
```
