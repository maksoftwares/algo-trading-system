# COMEX Round-Barrier Rejection V71

V71 tests whether concentrated liquidity around mechanically fixed COMEX gold
price levels creates a causal rejection signal for executable XAUUSD spot.

Exactly 1,000 policies are registered. Calibration can use only COMEX feature
density, active-day coverage, and direction balance. It cannot inspect any
post-decision spot quote or economic outcome.

Run sequentially:

```powershell
uv run --with-requirements requirements.txt python prepare_calibration.py
uv run --with-requirements requirements.txt python lock_contract.py
uv run --with-requirements requirements.txt python run_stage.py --stage development
```

Validation and exam remain sealed until every prior gate passes. This package
is historical research only and grants no model, EA, demo, live, payment, or
broker authority.
