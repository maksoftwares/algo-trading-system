# XAUUSD Cross-Asset Residual Directional Specialists V1

Frozen, non-optimized research lane for independently scoring negative-residual long and positive-residual short XAUUSD specialists using official Dukascopy Bid/Ask ticks and one causal rolling OLS model.

Bulk raw, normalized, bar and model evidence is stored outside Git through `DUKASCOPY_TICK_DATA_ROOT`. This lane is research evidence only; it is not MT5 parity, forward-shadow, deployment or trading authorization.

Run focused tests:

```powershell
python -m pytest tests -q
```

Run Stage A:

```powershell
$env:DUKASCOPY_TICK_DATA_ROOT='C:\DukascopyTickDataFoundationV1'
python run_research.py --stage-a
```
