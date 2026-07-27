# Claude XAUUSD ML and V8 Audit V1 — Preregistration

## Status of this document

**Written retrospectively on 2026-07-27**, after the experiments ran, to restate
work originally done in a conversational lane into the package format used by the
`v6-causal-ml-*` lanes so the two can be compared directly.

That retrospection is itself a limitation and is declared here: the gates below
were applied during the work and are recorded faithfully, but they were not
committed to a file before each run. **Treat the pass/fail tokens in this package
as weaker evidence than those in a genuinely pre-committed lane.** Nothing here
should be read as having the same standing as `v6-causal-ml-veto-v1` or
`v6-causal-ml-early-exit-v3`, which were preregistered before execution.

Where a gate was decided after seeing data, it is marked **[POST-HOC]**.

## Questions

Six lanes, run 2026-07-26 to 2026-07-27:

| Lane | Question |
|---|---|
| A | Does a per-regime specialist family beat a pooled one? |
| B | Does the XAUUSD mechanism transfer to EURUSD/GBPUSD/USDJPY/XAGUSD? |
| C | Does a horizon-diversified bidirectional family (GOLD V8) improve on V6? |
| D | Can an ML model close positions early, before the stop? |
| E | Can an ML model filter bad trades out of the V6 book? |
| F | Can cross-asset context size positions better than flat? |
| G | Can microstructure generate entries rather than only rank them? |

## Frozen decisions common to all lanes

- Signal feed: Dukascopy M5 bid/ask, 2016-07 to 2026-06.
- Execution feed: Capital.com M5. Trades whose entry bar has no Capital match are
  dropped as unexecutable.
- Mechanics inherited from V6 unless a lane states otherwise: confirmation entry
  at 0.5x stop, stop 6.75 x ATR144, exit at stop or horizon close, 07-17 UTC,
  30-minute decision grid.
- Fit boundary: trades **closing** on or before 2024-12-31. 2025-01 onward sealed.
- Profit factor is computed on the same dollar series as P&L and drawdown.

## Gates

| Lane | Gate |
|---|---|
| A | WR >= 50% and PF >= 1.8 on dev AND test, per regime |
| B | PF >= 1.20 on dev AND test, n >= 100, decided on each instrument's own record |
| C | must survive a causal walk-forward where every parameter is chosen from prior data |
| D | must beat the mechanical baseline "exit when unrealised R < -X"; scored on total R, not classification accuracy |
| E | must improve BOTH profit factor and total P&L on the sealed era, at a cutoff chosen from the fit era |
| F | must improve BOTH total P&L and return-per-drawdown, and survive rounding to whole 0.01-lot units |
| G | PF >= 1.20 on BOTH eras with n >= 150 each **[POST-HOC: reused lane B's gate]** |

## Governance

Historical research only. No lane in this package authorizes Python, EA, demo,
live, or broker execution. Failure quarantines the lane. The one partial pass
(lane C, fix C) still requires prospective evidence and runtime parity before any
authorization decision.
