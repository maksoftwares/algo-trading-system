# EURUSD Thousand-Strategy Campaign V1

This is an isolated, retrospective EURUSD strategy hunt inspired by the
XAUUSD fast-research funnel. It does not modify or compete inside the frozen
V1R RSI/Bollinger baseline package.

The campaign:

- freezes exactly 1,000 variants before opening outcomes;
- covers ten mechanically distinct long/short archetypes;
- uses raw Dukascopy EURUSD bid/ask history from July 2016 through June 2026;
- enters only on the next contiguous H1 bar;
- includes spread, adverse execution slippage, stop-first same-bar resolution,
  a maximum holding period, and an additional 0.5-pip stress;
- requires independent discovery-fit and discovery-confirm results;
- reports false-discovery-adjusted p-values across all 1,000 attempts;
- advances at most three variants per archetype;
- treats the H1 campaign as a rejection screen only.

No EA, MT5 execution, chart attachment, demo order, live order, or reviewer
submission is part of this lane.

Run:

```powershell
$env:DUKASCOPY_TICK_DATA_ROOT = "C:\DukascopyTickDataFoundationV1"
python run_campaign.py
```

The first run builds a deterministic external H1 bid/ask cache from the frozen
hourly raw JSON. The raw data and cache stay outside Git.
