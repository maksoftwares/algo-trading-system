# EURUSD H4 trend-pullback continuation preregistration

Date: 2026-07-30

Status: **FROZEN BEFORE OUTCOME**

Broker action: **forbidden**

## Purpose

The protected M15 sleeve is a short first-break strategy during 06:00–10:00
UTC. This experiment tests a distinct mechanism on later-session dates: H4
trend continuation after a completed H1 candle touches and rejects its
20-period EMA.

Two mirrored experts are fixed:

- H4 `trend_up`: long after an H1 EMA touch and bullish close above the EMA.
- H4 `trend_down`: short after an H1 EMA touch and bearish close below the EMA.

Only 10:00–19:00 UTC completed H1 bars may signal. Each expert may use only its
first signal per UTC date. Entry is the next M5 open, with a 0.7-pip minimum
retail spread, 0.1-pip adverse slippage per side, a 1.5 H1-ATR stop, 1.5R
target, 12-hour maximum hold, and stop-first same-bar handling.

## Information boundary

Development is 2017-01-01 through 2022-06-30. Each direction must independently
pass the frozen development sample, PF, stressed-PF, both-block, winner-removal,
and drawdown gates before its validation metrics are summarized.

Locked validation is 2022-07-01 through 2026-06-30. A selected expert must then
independently pass:

- at least 70 trades;
- PF at least 1.15 and +0.5-pip PF at least 1.10;
- PF above 1.0 in both two-year validation blocks;
- latest-12-month PF at least 1.10 and positive latest-six-month R;
- best-5%-removed PF at least 1.0;
- drawdown no more than 15R;
- five- and 15-minute entry-delay PF at least 1.0;
- at least 0.10 new dates per broker weekday;
- no more than 40% overlap with protected M15 active dates.

No parameter, clock, direction, year, stop, target, or subgroup rescue is
allowed after outcomes are opened. Historical success could authorize only a
disarmed forward-shadow candidate, never demo orders.

## Reproduction command

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_h4_trend_pullback_continuation.py
```

