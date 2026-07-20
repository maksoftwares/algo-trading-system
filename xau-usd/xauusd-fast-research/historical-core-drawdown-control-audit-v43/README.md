# Historical Core Drawdown-Control Audit V43

V43 attributes the USD 889.69 Core closed drawdown, applies the already-frozen
R1 box exposure cap without changing other specialists, verifies the capped R1
floating drawdown against ten years of Dukascopy data and exact raw quotes, and
computes fail-closed account-capital requirements.

Run the audit:

```powershell
uv run --with-requirements requirements.txt python run_audit.py
```

Run checks and lock the package:

```powershell
uv run --with-requirements requirements.txt python -m pytest -q
uv run --with-requirements requirements.txt ruff check .
uv run --with-requirements requirements.txt ruff format --check .
uv run --with-requirements requirements.txt python lock_contract.py
```

The audit is retrospective and read-only. It grants no training, EA, demo,
live, or broker authority.
