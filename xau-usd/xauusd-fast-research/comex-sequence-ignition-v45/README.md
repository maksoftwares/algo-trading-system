# COMEX Sequence-Ignition V45

V45 tests whether ordered aggressor-trade persistence and arrival acceleration
add a short-horizon XAUUSD edge beyond ordinary static COMEX flow summaries.
Read `PREREGISTRATION.md` before running the sealed workflow.

```powershell
uv run --with-requirements requirements.txt python prepare_calibration.py
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_stage.py --stage development
```

Validation and exam remain sealed unless every earlier stage passes. No command
in this package authorizes execution or model training.
