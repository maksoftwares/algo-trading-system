# Causal Candidate Quality Action Models V3

Offline, research-only action ranking and veto models for the expanded V3 gold
candidate population.

Three disjoint mechanical lanes are evaluated through six purged expanding
walk-forward folds. Each fold fits two frozen regressors, chooses one model and
retention policy using calibration data only, and evaluates it once on the test
partition. The benchmark is a calibration-ranked fixed-action cascade that
takes every eligible event.

No output authorizes MT5, Python serving, ML shadow, demo, live, or broker use.

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_evaluation.py
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt pytest -q
```
