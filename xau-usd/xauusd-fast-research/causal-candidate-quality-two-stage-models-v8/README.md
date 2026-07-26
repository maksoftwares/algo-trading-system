# Causal Candidate Quality Two-Stage Models V8

This research-only package separates two decisions that earlier pooled models
conflated:

1. Is there a positive stressed opportunity in this event?
2. Which available action horizon has the best relative outcome?

The event model uses 52 causal event features. The action model uses the frozen 58
V5 features plus 104 mechanical horizon interactions. Both stages use the same
calibration-selected training variant in each fold.

Run from this directory:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_evaluation.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt python -m pytest -q
```

All outputs are exposed development evidence. No model has shadow, demo, live, EA,
sizing, portfolio, or broker authority.
