# EURUSD H4 frequency reporting erratum

The first frequency-ladder reports counted every UTC date present in the source
as an "FX day." Dukascopy data includes a small Sunday UTC session, so that
reporting denominator included weekend dates.

The denominator now counts only Monday through Friday UTC dates. This changes
only the descriptive `trades_per_fx_day` field. Trade selection, fills, P&L,
profit factor, bootstraps, stress tests, chronological gates, and the frozen
20% frequency-selection gate all use trade counts rather than this denominator
and are unchanged.

After the first successful M15 outcome, the intrahour module also gained
monthly/yearly CSV exports and strict-JSON handling for an all-winning month's
infinite descriptive PF. Those changes are output formatting only. The
pre-outcome signal implementation is preserved at Git commit `f4282953`; the
trade ledger, P&L, selection result, and every frozen gate reproduced unchanged
after the reporting updates.
