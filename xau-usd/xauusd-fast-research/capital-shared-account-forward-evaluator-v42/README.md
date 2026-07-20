# Capital Shared-Account Forward Evaluator V42

V42 reconstructs the unchanged five-specialist Core and the locked V27
satellite family on the same untouched Capital quote stream. It measures actual
same-period frequency, P&L, overlap, floating equity drawdown, directional
exposure, and margin. It does not generate or reject signals.

Research passage and account readiness are separate decisions. In particular,
the current approximately USD 3,000 reference account and R5 fractional research
weights must not be mistaken for an executable sizing plan.

Run once with:

```powershell
uv run --with numpy --with pandas python run_evaluation.py
```

Run the read-only monitor with:

```powershell
uv run --with numpy --with pandas python run_evaluation.py --watch
```
