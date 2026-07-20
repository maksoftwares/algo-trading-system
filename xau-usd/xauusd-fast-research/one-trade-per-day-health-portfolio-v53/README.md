# One-Trade-Per-Day Health Portfolio V53

V53 keeps the accepted V50 Core unchanged and tests three separately identified
historical sleeves behind causal shadow-health and account-risk controls. It is
a terminal historical governance audit, not a pristine holdout or execution
authorization.

Run from the repository root:

```powershell
uv run --with pandas --with pyarrow python xau-usd/xauusd-fast-research/one-trade-per-day-health-portfolio-v53/lock_contract.py
uv run --with pandas --with pyarrow python xau-usd/xauusd-fast-research/one-trade-per-day-health-portfolio-v53/run_evaluation.py
```

