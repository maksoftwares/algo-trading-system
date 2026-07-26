# Capital Multi-Symbol Prospective V1 Preregistration

## Purpose

Capital's XAUUSD feed exposes bid/ask quote paths but no usable market depth,
reported volume, spread variation, or bid-versus-ask asymmetry. Existing
research has already tested single-symbol quote bursts, gap restarts, impulse
reversals, absorption releases, and fixed round-price reactions. Repeating
those mechanisms with new thresholds would not be independent research.

This package therefore adds synchronized external quote clocks before defining
another R3 or R4 strategy. It records gold, silver, the dollar index, US
equities, and two liquid FX pairs from the same broker and account.

## Frozen Boundary

- Exact account: `1033030`
- Exact server: `Capital.ComMena-Demo`
- Exact terminal: `C:/MT5PortableTier1BestEA/terminal64.exe`
- First admissible tick: `2026-07-27T00:00:00Z`
- Earlier July 22-24 observations are source-quality calibration only.
- No candidate direction, return, trade label, P&L, or strategy gate is
  selected from the calibration observations.

The collector may backfill from the boundary after a process restart, but it
must never write a tick earlier than the boundary.

## Frozen Symbols

`XAUUSD`, `XAGUSD`, `DXY`, `US500`, `EURUSD`, and `USDJPY`.

The set is fixed before forward outcomes. Adding or removing a symbol requires
a new data-foundation version and a later untouched boundary.

## Read-Only Contract

The collector may call only MetaTrader5 account, terminal, symbol-selection,
symbol-information, and tick-copy functions. It contains no order-send,
position-management, trade-request, or account-mutation path. All output rows
state that broker action, model training, Python prediction, EA consumption,
demo execution, and live execution are unauthorized.

Selecting a symbol in Market Watch is permitted only to make read-only tick
history available. It is not trading authority.

## Research Firewall

This foundation does not claim edge. A later specialist must:

1. define one causal mechanism before reading any post-candidate XAU outcome;
2. use completed information at or before each candidate timestamp;
3. count the new hypothesis in multiplicity control;
4. freeze execution geometry and realistic costs;
5. pass sequential untouched validation and confirmation;
6. remain outside V60 demo execution unless a separate authorization packet is
   approved.

