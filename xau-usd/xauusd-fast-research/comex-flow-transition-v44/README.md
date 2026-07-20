# COMEX Flow-Transition V44

V44 tests whether a causal flip in individual COMEX gold aggressor flow after
weak price response can supply the missing independent XAUUSD opportunity
density. Read `PREREGISTRATION.md` before running anything.

The calibration command opens candidate facts only:

```powershell
uv run --with-requirements requirements.txt python prepare_calibration.py
```

If calibration passes, freeze and verify the contract before opening economics:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_stage.py --stage development
```

Validation and exam remain sealed until every prior stage passes. No command in
this package authorizes model training, EA consumption, or broker action.
