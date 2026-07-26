# Causal Candidate Quality Expanded Dataset V3

Research-only expansion of the gold candidate-quality training population.

V3 promotes the hash-locked high-frequency mechanical ledger to a separate
primary learning population with one row per event/action pair. The existing
3,752-row canonical dataset remains a benchmark, and the journey archive remains
quarantined. No population is pooled silently.

V3 adds outcome-blind 30-minute structural episodes, weights that sum to one per
episode, purged expanding walk-forward assignments, overlap diagnostics, and an
immutable artifact manifest. It does not fit a model or authorize MT5 use.

Run:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python build_dataset.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt pytest -q
```
