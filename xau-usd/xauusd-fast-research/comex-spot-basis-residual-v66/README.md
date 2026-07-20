# COMEX-Spot Basis Residual V66

V66 evaluates a new roll-safe relative-value event clock using the already
downloaded zero-payment COMEX trade archive and Dukascopy XAUUSD bid/ask bars.
It never contacts Databento and keeps the 2025-2026 final year sealed during
selection.

## Result

All 288 registered policies were evaluated on 47,783 synchronized completed
bars spanning 773 sessions and 16 raw COMEX instruments. Zero policies passed
the three chronological pre-final gates, so the final year remained sealed.

- Sparse catch-up variants sometimes had high PF but only 1-9 trades in a year.
- The maximum minimum-window frequency was `0.146/day`; its economics failed.
- The best fade minimum-window stressed PF was `0.621`.
- Decision: `V66_NO_PREFINAL_SURVIVOR`.

Result SHA-256:
`582ac00a75e33363c9cd5d0bfb4e9c2d029b49a4f0fcd881241de86964fc9892`.
Metrics SHA-256:
`861d7ef0afa13e308a6e4d7ab053cd9a95106371ed03c263699fcab933368dcb`.
