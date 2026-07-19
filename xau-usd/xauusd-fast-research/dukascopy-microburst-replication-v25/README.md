# Dukascopy Microburst Replication V25

V25 is an exact cross-feed replication of the locked Capital V24.1
quote-microburst rule on the free Dukascopy XAUUSD bid/ask tick archive. It is
not a parameter search and it does not create a new signal definition.

The source window is fixed at 2016-07-01 through 2026-06-30. Source manifests,
the V24.1 implementation, every threshold, the 120-second label, costs, and
economic gates are locked before any Dukascopy microburst P&L is calculated.
Economic evidence opens in three chronological stages, at most one stage per
invocation. A failed stage is terminal for V25.

The Dukascopy archive has been used by earlier research, so V25 is honest
mechanism-level cross-feed evidence rather than an untouched final holdout. The
untouched Capital forward protocol remains required. Nothing in this package
authorizes model training, Python predictions, EA consumption, demo trading,
live trading, or broker action.
