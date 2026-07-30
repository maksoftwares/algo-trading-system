# EURUSD forward residual MT5 shadow-bridge protocol

## Purpose

The pre-outcome publisher proves that a residual side is selected before the
future path. The research evaluator's 20:00 quote cannot be used as executable
P&L for a signal received later.

This bridge captures the actual Capital.com demo-account bid and ask when the
published signal is received. That quote, not the research evaluator's entry,
is the execution reference for later live-only outcome adjudication.

The bridge is read-only. It cannot call an order-check, order-send, or
position-mutation API.

## Receipt boundary

Only the append-only live publisher ledger is accepted. A decision receives at
most one immutable bridge receipt.

- Cash decisions are mirrored without opening an MT5 API session.
- An eligible signal must be received within 120 seconds of publication.
- A late signal becomes immutable cash and cannot be recovered.
- The terminal must be the exact portable prospective collector.
- Account `1033669` on `Capital.ComMena-Demo` in demo trade mode is mandatory.
- The symbol must be exact `EURUSD`.
- The tick must be at most 15 seconds old.
- Bid and ask must be positive, ordered, and no more than 2.0 pips apart.

An invalid account, server, mode, symbol, clock, or quote fails the process
closed.

## Shadow entry

For a valid eligible signal:

- LONG uses the captured ask;
- SHORT uses the captured bid;
- lot size is fixed at 0.01;
- stop distance is eight pips;
- target distance is 12 pips; and
- maximum hold is six hours.

The receipt records the real tick time, bid, ask, spread, side, entry, stop,
target, and explicit false order/mutation flags. It records only
`WOULD_ENTER_LONG` or `WOULD_ENTER_SHORT`.

## Later evidence

The captured quote must later be adjudicated from raw broker ticks beginning no
earlier than the receipt tick. Research-evaluator P&L cannot substitute for
this live execution result.

## Prohibitions

No pre-floor receipt, backfill, late entry, stale tick, account or symbol
substitution, order check, order send, or position mutation is allowed.
