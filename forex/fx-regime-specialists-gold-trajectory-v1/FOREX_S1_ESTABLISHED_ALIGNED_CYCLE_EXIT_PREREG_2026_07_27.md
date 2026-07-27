# S1 Established-Aligned Next-Cycle Exit Preregistration — 2026-07-27

Status: `HASH_LOCKED_BEFORE_CYCLE_EXIT_OUTCOMES`

Boundary: offline research only. No MT5, broker, account, chart, EA attachment, or order action is authorized.

## Reason for This Trial

The frozen `S1 established aligned breakout` produced:

- 70 trades;
- PF 1.9058;
- +21.7983R;
- 3.0041R maximum drawdown;
- positive design, validation, and adaptive-exam windows;
- positive top-5%-winner removal and extra-cost stress.

It failed standalone admission solely because the three chronological windows contained 19, 27, and 24 trades rather than the required 30 each.

The frozen trade ledger also shows that open positions suppress later independently owned S1 signals. This trial is a single structural lifecycle test after alpha evidence, not a signal filter or parameter search.

## Frozen Components

The following remain byte-for-byte and logically unchanged:

- Dollar Index/Treasury/FX direction-volatility-phase classifier;
- shock abstention;
- `ESTABLISHED_ALIGNED` ownership;
- USDJPY 06:00–08:00 range construction;
- 08:00–12:00 M15 breakout evaluation;
- ATR, range-quality, candle, breakout-buffer, and close-location thresholds;
- long/short directions;
- stop geometry, 1R target, 900-point ceiling, and two-trades-per-day cap;
- next-M5 bid/ask entry;
- 0.1 pip adverse slippage on each side;
- quarantine interval;
- stop-first same-bar policy;
- chronological windows and all standalone admission gates.

No signal threshold, regime threshold, direction, session, stop, target, or cost assumption may change.

## Only Permitted Change

If neither stop nor target has closed the position, close it at the first executable M5 quote stamped 06:00 UTC on the next later active FX date.

- Long: exit at bid open minus 0.1 pip.
- Short: exit at ask open plus 0.1 pip.
- Stop and target remain active through the bar immediately before that cycle boundary.
- The 06:00 boundary bar is a time exit and is not evaluated for the old position's stop or target.

Economic rationale: the signal is owned by one London range-and-breakout episode. Carrying it into the next active 06:00–08:00 range allows one episode to suppress the next and mixes lifecycle ownership. Flattening at the next setup-cycle boundary restores one-event/one-cycle ownership.

## Admission

The unchanged specialist gates apply:

- at least 30 trades in each chronological window;
- PF at least 1.10 in each window;
- expectancy above +0.02R in each window;
- overall max drawdown no more than 12R;
- positive after top 5% winner removal;
- positive under another 0.5-pip round-trip stress.

Failure closes this exact lifecycle repair. The gate may not be relaxed afterward.

## Last Six Completed Months

After the full-window result is frozen, publish a separate report for `2026-01-01T00:00Z` through `2026-06-30T23:59:59Z` containing:

- complete trade ledger;
- monthly trades, net R, PF, win rate, and maximum drawdown;
- overall result and extra 0.5-pip stress;
- exit-reason and direction splits;
- an illustrative 0.01-lot USD P/L calculation.

This six-month slice is already part of the adaptive exam. It is a requested historical backtest, not untouched confirmation and not a promotion dataset.
