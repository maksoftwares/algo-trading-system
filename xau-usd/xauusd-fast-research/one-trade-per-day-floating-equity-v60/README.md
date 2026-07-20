# One Trade Per Day Floating Equity V60

This package performs a source-hashed, fail-closed whole-account floating-equity
audit of the unchanged V59 portfolio. It reconstructs source prices, combines
2010-2026 Dukascopy bid/ask M5 data, and evaluates both the locked P&L case and an
extra native-R1 fee-stress case against the inherited capital gate.

Run from this directory:

```powershell
uv run --with pandas --with numpy --with pyarrow python lock_contract.py
uv run --with pandas --with numpy --with pyarrow python run_evaluation.py
uv run --with pytest --with pandas --with numpy --with pyarrow pytest -q
```

Historical research only. This package cannot authorize trading.
