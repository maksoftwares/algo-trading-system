# EURUSD RSI health-gate prospective observer preregistration

Frozen before prospective observation begins: 2026-07-30.

Prospective floor: 2026-08-01 00:00 UTC.

Persistent observer identity: 26073093.

This package is a disarmed observer, not a trading EA. Its MQL5 source has no
trade library, order object, or order-send path. The terminal startup
configuration also sets `AllowLiveTrading=0` and `AllowDllImport=0`.

## Exact frozen virtual strategy

- EURUSD M15, long only.
- Completed-bar RSI(14) less than or equal to 30.
- Completed close below the Bollinger(20) middle line.
- Candle body at least 40% of range.
- Entry at the next M15 bar's first observed ask plus 0.1 pip adverse
  slippage.
- Entry hours 01, 07, and 21 UTC are blocked.
- Maximum entry spread: 10 pips.
- One virtual position at a time and no more than 20 virtual entries per UTC
  day.
- Stop is the lower of the most recent six completed M15 lows and 1.4 ATR(14)
  below entry, with a 3-pip floor and 70-pip ceiling.
- Target is 0.8R.
- Stop is checked before target on every tick.
- Virtual exit receives another 0.1 pip adverse slippage.

## Exact frozen health gate

All qualifying virtual trades remain in the shadow book, including trades the
gate rejects. Before each new virtual entry, the observer uses only completed
prior virtual outcomes. Admission requires exactly the latest 30 completed
outcomes to have profit factor at least 1.05. The first 30 virtual entries
cannot be admitted.

## Persistence and evidence integrity

The virtual position, daily count, M15 latch, 30-outcome ring buffer, and
contract identity are persisted in terminal global variables. A missing or
incompatible field causes initialization to fail. The observer does not
backfill missed bars after downtime and does not consume any observation before
the prospective floor.

Changing the signal, exit, cost, health-window, threshold, or start time creates
a different experiment. Historical results cannot authorize demo orders.

The first warm-up checkpoint is 30 completed raw virtual trades. A decision
checkpoint requires at least 120 completed raw trades, at least 60
health-admitted trades, at least 60 complete prospective weekdays, base PF at
least 1.15, 0.5-pip stressed PF at least 1.05, top-5%-winner-removed PF at least
1.00, and no source or state-integrity failure. Until every requirement passes,
demo-order authorization remains false.
