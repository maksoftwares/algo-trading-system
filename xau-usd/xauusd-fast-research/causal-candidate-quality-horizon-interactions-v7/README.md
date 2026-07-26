# Causal Candidate Quality Horizon Interactions V7

This research-only package gives Adaptive V5's ridge model context-dependent action
horizon slopes through a mechanical 104-feature interaction block. It changes no
candidate, label, fold, threshold grid, training variant, model class, or gate.

Run from this directory:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_evaluation.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt python -m pytest -q
```

All outputs are exposed development evidence. No model has shadow, demo, live, EA,
sizing, portfolio, or broker authority.
