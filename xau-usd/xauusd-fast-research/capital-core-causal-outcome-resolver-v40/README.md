# Capital Core Causal Outcome Resolver V40

This read-only service turns frozen V28, V29, and V34 candidate facts into
append-only, causally observed Capital bid/ask labels. It leaves all candidate
collectors unchanged and publishes no aggregate economics.

Lock and verify:

```powershell
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python verify_historical_semantics.py
```

Run one cycle:

```powershell
uv run --with-requirements requirements.txt python run_resolver.py --once
```

The runtime is
`C:\MT5PortableProspectiveCollector\MQL5\Files\core_outcomes_v40`.
