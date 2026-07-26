# Causal Loss-Signature One-Class V1

Offline experiment fitting an Isolation Forest exclusively on historical
losing trades from corrected Expanded Dataset V4. Winners are used only in
chronological test evaluation.

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_experiment.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt pytest -q
```

This package has no runtime, MT5, shadow, demo, live, or broker authorization.

