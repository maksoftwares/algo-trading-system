# Causal Candidate Quality Pairwise Models V9

This offline package combines a binary event-tradeability classifier with a
pairwise fast/intraday/swing action ranker. Pairwise probabilities are aggregated
with a deterministic Borda score, while event retention remains calibration-only.

Run from this directory:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_evaluation.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt python -m pytest -q
```

All outputs are exposed development evidence. No model has shadow, demo, live, EA,
sizing, portfolio, or broker authority.
