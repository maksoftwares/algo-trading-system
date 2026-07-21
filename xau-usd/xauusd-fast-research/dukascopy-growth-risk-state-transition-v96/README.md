# V96 Dukascopy Growth-Risk State Transition

Run only after the source foundation is hash-bound, V94 has failed terminally,
and V95's committed pre-outcome lock failure is verified:

```powershell
uv run --with pandas --with numpy --with pyarrow --with scipy python lock_contract.py
uv run --with pandas --with numpy --with pyarrow --with scipy python run_research.py discovery
```

Confirmation, Final, and the shared audit remain sealed by their advancement
locks. V96 is retrospective research only and grants no training or execution
authority.
