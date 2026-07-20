# Capital Forward Handoff Watch V67

V67 closes an operational scheduling gap between the locked Capital forward
collectors and the locked V27 family evaluator. V24.1 and V26 create their
sealed stage artifacts independently, while V27 is intentionally a one-shot
program. This package periodically invokes that unchanged program so a newly
completed stage is evaluated without a manual launch.

V67 does not generate signals, read trade outcomes for selection, calculate
portfolio economics, or alter any V24.1, V26, V27, or V42 file. The child V27
process performs its own contract and artifact verification. V67 records only
process health, collector inventory counts, and the latest self-hashed status or
stage decision already published by V27.

Nothing in this package authorizes model training, Python predictions, EA
consumption, demo trading, live trading, or broker action.

## Run

One health cycle:

```powershell
uv run --with-requirements requirements.txt python run_watch.py
```

Continuous polling:

```powershell
uv run --with-requirements requirements.txt python run_watch.py --watch
```
