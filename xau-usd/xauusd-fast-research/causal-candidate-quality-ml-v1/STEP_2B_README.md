# Step 2B: Dataset and Feature Contract Lock

Step 2B freezes the exact population, label replay, causal features,
deduplication, weights, walk-forward splits, costs, and missing-data behavior
before any economic outcome is opened.

Run:

```powershell
uv run --no-project --with-requirements requirements.txt python run_step_2b_lock.py
```

Passing this gate authorizes only Step 3 counterfactual label and causal feature
construction. Model fitting, threshold fitting, portfolio simulation, ML
shadowing, and runtime changes remain unauthorized.
