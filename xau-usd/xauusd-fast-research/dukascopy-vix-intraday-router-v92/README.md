# Dukascopy Intraday VIX Router V92

V92 tests whether free intraday Dukascopy `VOL.IDX/USD` information can add
independent XAUUSD opportunities to byte-identical V59/V60. The only acceptance
target is at least two combined trades per weekday in Development-2,
Confirmation, and Final after costs, routing, correlation, and floating-equity
controls.

Run only in this order:

```powershell
uv run --with pandas --with pyarrow --with scipy python lock_contract.py
uv run --with pandas --with pyarrow --with scipy python run_research.py discovery
uv run --with pandas --with pyarrow --with scipy python run_research.py confirmation
uv run --with pandas --with pyarrow --with scipy python run_research.py final
uv run --with pandas --with pyarrow --with scipy python run_shared_audit.py
```

Each later command remains sealed unless the prior stage selected an unchanged
policy. A terminal failure cannot be rescued inside V92. This package is
research-only and grants no model-training, EA, demo, live, payment, Databento,
or broker authority.
