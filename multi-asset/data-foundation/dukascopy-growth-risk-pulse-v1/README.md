# Dukascopy Growth-Risk Pulse Foundation V1

This source-only package acquires official Dukascopy best-bid/best-ask ticks for
three previously unused XAU context instruments:

- `USA500.IDX/USD` for US risk appetite;
- `COPPER.CMD/USD` for global and China-sensitive growth pressure;
- `USD/CNH` for offshore China and dollar stress.

Raw JSON responses are validated and stored as deterministic gzip files. The
uncompressed source SHA-256 remains in every acquisition manifest, so the exact
official response is recoverable and independently verifiable without consuming
the disk space of expanded JSON. Curated M5 bars contain source features only.

## Commands

```powershell
uv run --with httpx python acquire.py --symbol USA500IDXUSD
uv run --with httpx python acquire.py --symbol COPPERCMDUSD
uv run --with httpx python acquire.py --symbol USDCNH
uv run --with pandas --with numpy --with pyarrow python build.py
uv run --with pytest --with pandas --with numpy pytest -q
```

Each acquisition command is resumable at the hourly-file level. This package
does not open XAUUSD outcomes, construct labels, score strategies, train a model,
or authorize broker activity.
