# XAUUSD ML Candidate Rankers V1

Research-only walk-forward test of two mechanically distinct M15 candidate
families ranked by shallow Python models using causal price and Dukascopy
microstructure features.

```powershell
uv run --with pandas --with numpy --with pyarrow --with scikit-learn --with pytest python run_research.py
```

The models rank predefined candidates. They do not generate unrestricted buy or
sell decisions and cannot authorize EA, demo, or live execution.
