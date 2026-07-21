# Dukascopy Intraday Volatility Index Foundation V1

This package acquires free, official Dukascopy `VOL.IDX/USD` ticks and builds a
causal M5 feature cache outside Git. It is a source foundation only. It does not
read XAUUSD outcomes, score a strategy, authorize a model, or authorize trading.

The default external storage root is `C:/DukascopyVolIndexFoundationV1`. Raw
hourly responses are validated, hashed in monthly acquisition manifests, and
made read-only before the curated cache is built.

```powershell
uv run --with pandas --with httpx python acquire.py
uv run --with pandas --with pyarrow python build.py
```

The source window is `2023-01-01` through `2026-06-30`. Empty official hourly
responses are retained because they are part of the coverage audit.
