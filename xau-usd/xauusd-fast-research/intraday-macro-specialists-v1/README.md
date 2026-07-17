# XAUUSD Intraday Macro Specialists V1

Research-only screen of three mechanical XAUUSD specialists using synchronized
Dukascopy M5 dollar-index and US Treasury total-return data.

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn --with pytest python -m pytest -q
uv run --with pandas --with numpy --with pyarrow --with scikit-learn python run_research.py
```

The campaign uses native XAUUSD Bid/Ask execution and frozen stress costs. No
result from this directory authorizes Python prediction, EA consumption, demo,
or live execution.
