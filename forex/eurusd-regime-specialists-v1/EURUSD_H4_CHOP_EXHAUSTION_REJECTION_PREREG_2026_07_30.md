# EURUSD H4 chop exhaustion-rejection preregistration

Date: 2026-07-30

Status: **FROZEN BEFORE OUTCOME**

Demo-order authorization: **false**

## Hypothesis

Chop is the largest single H4 state among the weekdays left empty by protected
M15. This experiment tests a different economic mechanism during 10:00–19:00
UTC: fade an H1 excursion beyond a fixed EMA20 plus or minus 0.75 H1-ATR
envelope only when the completed candle rejects the excursion and closes back
inside the envelope.

The rule is symmetric. A lower-envelope bullish rejection enters long; an
upper-envelope bearish rejection enters short. Only the first qualifying
direction per UTC date is retained. One position may be open across both
directions.

Execution is fixed at the next M5 open with retail bid/ask, a 0.7-pip spread
floor, 0.1-pip adverse slippage per side, 1.5 H1-ATR stop, 1.5R target,
12-hour maximum hold, and stop-first same-bar resolution.

## Locked procedure

The single two-sided expert must pass all development gates on 2017 through
2022H1 before 2022H2 through 2026H1 validation is summarized. Both directions
must have enough trades and avoid material standalone loss. Validation also
requires cost and entry-delay robustness, positive chronological blocks,
recent survival, winner-removal resilience, and at least 0.10 genuinely new
active dates per broker weekday with no more than 40% protected-date overlap.

No side deletion, clock or envelope search, threshold adjustment, year mask,
or stop/target repair is allowed after outcomes are opened.

## Reproduction command

```powershell
uv run --offline --with pandas --with numpy --with pyarrow python run_h4_chop_exhaustion_rejection.py
```

