# V60 Whole-Account Floating-Equity Preregistration

## Purpose

V59 passed the locked closed-trade frequency and edge gates after native-position
and broker-lot correctness repairs. V60 asks one new question: does that exact,
unchanged portfolio remain inside the inherited account equity-drawdown limit while
positions are open?

## Frozen Inputs

- Use the exact V59 broker-expressible Core and accepted trade ledger.
- Reconstruct all 2,194 accepted trades one-to-one from native MT5 position prices
  or the sealed Dukascopy raw-tick execution ledgers.
- Use Dukascopy bid/ask M5 bars from 2010-01-01 through 2026-06-30.
- Do not change a signal, threshold, risk amount, accepted row, or V59 gate.
- Fail closed on an unmatched row, duplicate match, timestamp mismatch, direction
  mismatch, P&L mismatch, missing quote, or changed source hash.

## Mark-To-Market Rule

At 0.01 XAUUSD lots, one USD of price movement equals one USD of P&L. Longs are
marked on bid and shorts on ask. For each M5 bar:

- favorable equity uses `bid_high` for longs and `ask_low` for shorts;
- adverse equity uses `bid_low` for longs and `ask_high` for shorts;
- bar-close equity uses `bid_close` for longs and `ask_close` for shorts;
- a trade overlapping any part of a boundary bar is exposed to that full bar's
  extrema, intentionally overstating risk;
- favorable equity is allowed to precede adverse equity inside the same M5 bar,
  which is the conservative ordering for drawdown;
- nonnegative implied execution cost is charged in full at entry;
- a negative implied cost or rebate is not credited while the trade is open and is
  recognized only in its locked close result.

The final realized endpoint must reconcile exactly to the V59 locked P&L.

## Locked Capital Gate

- Starting equity: USD 2,998.45.
- Hard equity-drawdown limit: 15%, or USD 449.7675.
- Required safety buffer: 25%.
- Therefore raw measured floating drawdown must be no more than USD 359.814.
- The same gate must pass after an additional USD 0.30 charge on every native R1
  trade because the native export lacks complete `DEAL_FEE` evidence.
- All inherited V59 frequency, profitability, robustness, and closed-drawdown gates
  must remain passed.

No post-result V60 tuning is allowed. A failed result is terminal for V60 and may
only be addressed by a separately preregistered portfolio-control version.

## Claims

Passing V60 would prove historical conservative M5 floating-equity compatibility
for this fixed research portfolio. It would not prove MT5 portfolio parity,
prospective performance, Python execution readiness, demo readiness, or live
readiness.
