# V60 Causal Protection-Action Utility V21

Read-only, outcome-exposed diagnostic of causal state at frozen Dynamic V6
`OPEN_PROFIT_GIVEBACK` actions. It cannot place orders or authorize deployment.

```powershell
uv run --with-requirements requirements.txt python run_diagnostic.py
uv run --with-requirements requirements.txt python -m pytest tests -q
```

V21 first replays unmodified Dynamic V6 and an observational subclass against
the same immutable quote cache. Any event-path difference invalidates the
diagnostic. Only then does it run the single preregistered expanding-year ridge
model.

