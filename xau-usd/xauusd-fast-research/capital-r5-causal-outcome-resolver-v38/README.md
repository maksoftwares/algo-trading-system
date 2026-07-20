# Capital R5 Causal Outcome Resolver V38

This read-only service turns frozen V35 R5 candidate facts into append-only,
causally observed Capital bid/ask labels using the frozen V9 execution rules.

Lock and verify:

```powershell
uv run --with numpy --with pandas --with pyarrow python lock_contract.py
uv run --with numpy --with pandas --with pyarrow python verify_historical_semantics.py
```

Run one cycle:

```powershell
uv run --with numpy --with pandas --with pyarrow python run_resolver.py --once
```

The runtime is
`C:\MT5PortableProspectiveCollector\MQL5\Files\r5_transition_outcomes_v38`.
`r5_component_resolutions.jsonl` is append-only. `runtime_status.json` exposes
counts and safety state but no aggregate P/L.
