# Causal Candidate Quality Macro Models V6

This research-only package replays the locked Adaptive V5 action-ranking experiment
with eight causal DXY and Treasury state features. It preserves the corrected V4
population and all V5 training, calibration, stress, bootstrap, and acceptance rules.

The broader XAGUSD/EURUSD/USDJPY cache is deliberately excluded because it ends in
June 2024 and cannot evaluate the latest folds. Macro gaps are handled by fit-only
median imputation without missingness indicators; candidate rows are not dropped.

Run from this directory:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_evaluation.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt python -m pytest -q
```

All outputs are development evidence. No model has shadow, demo, live, EA, sizing,
portfolio, or broker authority.
