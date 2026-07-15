# XAUUSD Cross-Asset Residual Shock Continuation V1

This frozen research lane tests one hypothesis: an extreme, contemporaneous XAUUSD M5 return residual continues in its own direction. Positive shocks create long candidates and negative shocks create short candidates.

Only official Dukascopy native Bid/Ask ticks are accepted. The 2021-07 through 2024-06 hypothesis-generation period is quarantined and cannot enter scoring. Stage A is 2018-07 through 2021-06. Stage B is inaccessible unless a direction passes every Stage A gate.

Run from this directory with `DUKASCOPY_TICK_DATA_ROOT` set to the external data root:

```powershell
python run_research.py --stage-a --concurrency 4
python -m pytest tests -q
python run_research.py --finalize --test-result "N passed"
```

This is research evidence only. It is not MT5 parity, forward-shadow, EA, deployment, or trading authorization.
