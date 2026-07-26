# Causal Canonical Auxiliary Transfer V15

V15 is a separate offline experiment. It leaves the frozen V14 prospective
lane unchanged.

The experiment uses the corrected high-frequency candidate dataset as an
auxiliary learning population. Exact and near-duplicate 30-minute episodes
that overlap the canonical benchmark are removed first. Three auxiliary
signals are then learned from both winning and failing actions:

- linear stressed Expected-R;
- nonlinear stressed Expected-R; and
- probability of a positive stressed return.

Those signals become three additional causal inputs to the nine-family
canonical Expected-R model. Thresholds are selected only on canonical
calibration rows, and the final result is measured by an exact V60 portfolio
replay with the current post-loss cooldown.

Run in order:

```powershell
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe lock_contract.py
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe run_evaluation.py
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe verify.py
& ..\balanced-horizon-ml-v5\.venv\Scripts\python.exe -m pytest -q
```

All outputs are historical research. V15 cannot score prospective candidates,
modify MT5, filter demo trades, size positions, or place broker orders.
