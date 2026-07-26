# Causal Candidate Quality Expanded Dataset V4

Correction-only expanded causal dataset built from Complete Candidate Dataset
V5. It preserves V3 identities, labels, structural weights, and folds while
replacing the two mis-scaled prior-event features.

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python build_dataset.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt pytest -q
```
