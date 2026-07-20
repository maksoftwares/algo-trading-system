# Causal Unused-Event Router V61

Run the development-only grid:

```powershell
uv run --with-requirements requirements.txt python run_discovery.py
```

The experiment preserves V59 trades, excludes all previously qualified V57
events, and writes the 48-policy development table under `outputs/`.
