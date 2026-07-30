# EURUSD prospective multi-symbol collector v1

This package collects new, untouched EURUSD and cross-pair observations for the
next causal strategy-development stage. It is an observer, not a trading
strategy.

The collector:

- runs only in MetaTrader 5 Strategy Tester or on a demo account;
- must be attached to the exact configured EURUSD symbol on M5;
- contains no trade library, order function, or position-management path;
- starts with a latch and never backfills the bar that existed at startup;
- captures only the just-completed native M5 interval;
- uses `CopyTicksRange` independently for every configured symbol;
- records missing symbols and missing ticks instead of forward-filling them;
- writes raw quote aggregates, environment metadata, and heartbeats to the
  terminal Common Files directory;
- treats Strategy Tester output as smoke-test evidence only; and
- refuses live observations before the frozen forward boundary
  `2026.08.01 00:00` UTC.

The default source list is:

`EURUSD,EURGBP,EURJPY,GBPUSD,USDJPY,GBPJPY,DOLLARIDXUSD,USTBONDTRUSD`

The last two names are optional broker feeds. A broker using suffixes or
different index names must receive an edited, frozen preset before collection.
Unavailable sources remain explicit `SYMBOL_UNAVAILABLE` rows.

## Files written

The safe preset writes three CSV files under the MT5 Common Files directory:

- `EURUSD_PROSPECTIVE_M5_FEATURES_V1.csv`
- `EURUSD_PROSPECTIVE_M5_ENVIRONMENT_V1.csv`
- `EURUSD_PROSPECTIVE_M5_HEARTBEAT_V1.csv`

The feature ledger has one row per source symbol and completed EURUSD M5
interval. It records first/last timestamps, bid and ask OHLC, quote counts, and
spread statistics. It does not create outcome labels or trade decisions.

## Operating boundary

This component does not improve the current backtest and does not prove a
daily-frequency edge. It creates the first genuinely untouched evidence that
can support or reject a future specialist. The validated H4 strategy remains a
separate protected sleeve.

See `PROSPECTIVE_DATA_PROTOCOL.md` for the frozen evidence and admission rules.

