# XAUUSD Cross-Asset Residual Directional Specialists V1 — Review Corrections

Frozen, non-optimized research lane for independently scoring negative-residual long and positive-residual short XAUUSD specialists using official Dukascopy Bid/Ask ticks and one causal rolling OLS model.

Bulk raw, normalized, bar and model evidence is stored outside Git through `DUKASCOPY_TICK_DATA_ROOT`. This lane is research evidence only; it is not MT5 parity, forward-shadow, deployment or trading authorization.

This branch is a correction-only evidence replay of reviewed commit `0722a66a41cf7a3d109a4bc129f8f469b80ca022`. It does not change the strategy, model, parameters, features, direction, filters, or Stage A period. Stage B is prohibited.

Run focused tests:

```powershell
python -m pytest tests -q
```

Run the two independent corrected Stage A derivations:

```powershell
$env:DUKASCOPY_TICK_DATA_ROOT='C:\DukascopyTickDataFoundationV1'
python run_research.py --review-corrections
```
