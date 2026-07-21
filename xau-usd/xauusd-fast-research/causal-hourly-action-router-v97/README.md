# V97 Causal Hourly Action Router

V97 tests a dense symmetric H1 action lattice with regularized causal ranking.
It is additive to byte-identical V59/V60 and conditional on terminal V96.

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_research.py discovery
```

Confirmation, Final, and the shared audit remain sealed by their advancement
locks. Research-model fitting is allowed; deployment and trading are not.
