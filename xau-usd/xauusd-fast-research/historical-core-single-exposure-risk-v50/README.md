# Historical Core Single-Exposure Risk Control V50

V50 tests and locks a prospective one-position R1 box exposure rule after V43
identified R1 stacking as the cause of the USD 889.69 closed drawdown.

Run from this directory:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py --write
uv run --with-requirements requirements.txt python lock_contract.py --verify
uv run --with-requirements requirements.txt python run_audit.py
uv run --with-requirements requirements.txt pytest -q
```

This package is research and risk governance only. It does not authorize model
training, Python prediction, EA consumption, demo trading, or live trading.
