# V60 Canonical Demo Portfolio V2

This additive deployment package binds the frozen V59/V60 XAUUSD portfolio to
demo account `1033030`. It contains the five Core specialists plus the four
canonical add-on sleeves. The frozen research packages and their ledgers are
not modified.

The runtime has no model inference, model handoff, ML ranker, or ML shadow
path. It fails closed if the active MT5 chart profile contains a legacy Phase2
executor, an A3 ML observer, or an enabled ML shadow read tap.

Demo broker action is enabled for exact account `1033030` after the feed,
profile, account, historical-parity, currency-conversion, guardian-halt, and
broker `order_check` gates passed. Live trading remains unauthorized. Runtime files live beneath
`C:/MT5PortableTier1BestEA/MQL5/Files/v60_canonical_demo_v2`.

The account is AED-denominated. Every USD drawdown threshold is converted using
the AED peg (`3.6725 AED/USD`) before it is compared with MT5 equity or deal
values.

The MT5 profile keeps both account guardians and attaches one passive telemetry
collector plus three observer-only event sensors. Each collector/sensor has
per-EA trading disabled. The Python portfolio executor is the only component
authorized to open canonical trades; the armed daily guardian may close trades
and create its halt file.

Use `start_portfolio.ps1` after a restart. It starts one feed process and one
portfolio process and refuses duplicate launchers. Healthy execution reports
`ACTIVE_DEMO_BROKER_ACTION` in `status.json`; `feed_status.json` must report all
eight required feed groups healthy. `set_terminal_algo_trading.ps1` changes the
terminal-wide Algo Trading state only while that terminal is stopped, and keeps
a backup of `common.ini`.

The older `v60-core-demo-executor-v1` package is superseded and must not run at
the same time as this full canonical package.
