# Capital R5 Causal Router V39

This read-only service applies the frozen V11 R5 component router to V35
candidates using historical V9 outcomes plus only causally available V38
prospective outcomes.

```powershell
uv run --with numpy --with pandas --with pyarrow python lock_contract.py
uv run --with numpy --with pandas --with pyarrow python verify_historical_parity.py
uv run --with numpy --with pandas --with pyarrow python run_router.py --once
```

Runtime files are written under
`C:\MT5PortableProspectiveCollector\MQL5\Files\r5_transition_router_v39`.
The routed ledger is append-only and contains no realized candidate outcome.
