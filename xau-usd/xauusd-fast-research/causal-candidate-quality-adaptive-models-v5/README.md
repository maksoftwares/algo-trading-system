# Causal Candidate Quality Adaptive Models V5

Research-only comparison of expanding, rolling, recency-weighted, and
regime-local ridge models on corrected Expanded Dataset V4.

Selection is nested inside each walk-forward fold: FIT trains, CALIBRATION
chooses one frozen variant and threshold, and TEST evaluates it once. Outputs
do not authorize MT5, serving, shadowing, demo, live, sizing, or broker action.

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_evaluation.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt pytest -q
```
