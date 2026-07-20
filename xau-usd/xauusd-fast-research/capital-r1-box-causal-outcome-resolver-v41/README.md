# Capital R1 Box Causal Outcome Resolver V41

This read-only service converts the frozen `R1_UPTREND_LONG_V1` candidate stream
into append-only Capital bid/ask outcomes. It enforces the decision-eligible
two-position, one-entry-per-UTC-day policy and leaves the source observer
unchanged.

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
`C:\MT5PortableProspectiveCollector\MQL5\Files\r1_box_outcomes_v41`.
