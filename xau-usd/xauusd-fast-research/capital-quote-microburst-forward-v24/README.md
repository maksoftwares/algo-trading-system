# Capital Quote Microburst Forward V24

V24 is a single, forward-only XAUUSD quote-microstructure hypothesis. It uses
millisecond Capital demo quotes already produced by the read-only prospective
collector. The historical calibration step may inspect schema, data quality,
causal feature distributions, and candidate counts only. It must never calculate
post-candidate prices, returns, P&L, win rate, or regime performance.

The implementation is frozen before the forward window starts at
2026-07-20 00:00 UTC. The first 20 complete evidence weekdays form sequential
validation. Confirmation remains sealed until validation passes unchanged and a
second set of 20 complete weekdays exists.

Nothing in this package authorizes Python prediction, EA consumption, demo
trading, live trading, or broker action.
