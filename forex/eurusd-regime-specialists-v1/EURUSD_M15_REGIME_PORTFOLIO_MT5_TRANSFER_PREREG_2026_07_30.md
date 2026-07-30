# EURUSD M15 regime-portfolio MT5 transfer preregistration

Status: **FROZEN_BEFORE_BROKER_TRANSFER_OUTCOME**

The selected Dukascopy M15 first-break portfolio is transferred once to
Capital.com real ticks from `2024-07-01` through `2026-06-30`. This is a broker
and implementation transfer, not a new parameter search.

The rule remains:

- completed M15 bars;
- 00:00–05:59 UTC reference range;
- 06:00–09:59 UTC decision bars;
- the first qualifying downside break for each causal H4 regime and UTC date;
- SHORT only;
- chop body fraction at least 0.35 and compression at least 0.55;
- 1.75 times the latest available H1 ATR stop;
- 1.25R chop target and 2.0R compression target;
- 12-hour maximum hold; and
- fixed 2:1 chop/compression allocation.

The tester uses 0.02 lot for chop and 0.01 lot for compression so the broker can
execute the frozen relative allocation. Dollar results are divided by two when
reported as the historical research-lot equivalent.

The one-shot transfer requires at least 100 trades, at least 0.20 trades per
weekday, full PF at least 1.10, PF above 1.0 in each chronological 12-month
half, latest-12-month PF at least 1.10, positive net P&L, PF at least 1.0 after
removing the best 5% of trades, and balance drawdown no greater than 2%.

No regime, side, clock, threshold, stop, target, or allocation may be changed
after the result. Even a pass cannot authorize demo orders; it only permits an
unchanged prospective shadow run.
