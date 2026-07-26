# Canonical Expected-R Prospective V13

Locked read-only forward confirmation for the historically qualified Expected-R
V11 policy.

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_evaluation.py --once
uv run --with-requirements requirements.txt python verify.py
uv run --with-requirements requirements.txt pytest -q
```

Runtime evidence is written under
`D:/AlgoTradingData/prospective/causal-canonical-expected-r-prospective-v13`.
Nothing in that directory is consumed by MT5. Both the baseline and retained
model scenarios are evaluated through the locked V60 account-routing policy,
including V57's same-direction 120-minute post-realized-loss cooldown, with
two-stage sample, family-coverage, and weekly-block confidence gates.
