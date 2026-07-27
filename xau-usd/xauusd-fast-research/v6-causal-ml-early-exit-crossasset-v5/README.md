# V6 Causal ML Early Exit Cross-Asset V5

This offline lane tests one preregistered explanation for V4's failure. V4
identified many exits that avoided losses, but rare recoveries made its total
economic benefit negative. V5 asks whether completed DXY, US Treasury,
EURUSD, GBPUSD, and USDJPY bars can distinguish a temporary XAUUSD setback
from continued failure.

V5 freezes V4's population, target, quantile model, action guards, checkpoints,
costs, annual walk-forward boundaries, routing, and gates. The only model
change is a small causal cross-asset feature block.

All source bars must be complete before the decision time. A backward join may
be at most 10 minutes stale, and data is never filled across a market closure.
Missing returns are represented by zero together with explicit availability
flags.

Text locks accept exact bytes or a recorded CRLF-to-LF
normalization only. This accommodates Git checkout line endings without
allowing any content drift. Binary inputs always require exact bytes.

Historical success cannot authorize Python prediction, EA consumption, demo,
live, or broker use.

Run:

```powershell
python run_experiment.py
```

Test:

```powershell
python -m pytest -q
```

The locked run failed and is quarantined. See `POST_RUN_DECISION.md` and the
generated result in `outputs/`.
