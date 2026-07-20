# Two-Trade-Per-Day Locked Router V62

Lock, then evaluate exactly one development-selected policy:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_evaluation.py
```

V62 preserves every V59 trade and treats any required-window gate failure as a
rejection.
