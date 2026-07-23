# EURUSD regime specialists V2

This package implements the XAU-style architecture requested for EURUSD:
an explicit H4 classifier, independent regime specialists, an unsafe/no-trade
state, sequential gates, and a router that cannot hide a failed component.

Run:

```powershell
python run_research.py
```

Outputs are written to `outputs/`.

## Current demo result

The Dukascopy-first candidates did not transfer to Capital.com and are sealed.
The broker-native V2 hunt produced `EURCAPV2_CHOP_ASIA_LONDON_SHORT`. Its
Capital.com real-tick MT5 exam (2024-07 through 2026-06) returned:

- 62 trades
- 53.23% win rate
- profit factor 1.45
- +$22.85 at 0.01 lot
- 0.11% maximal balance drawdown
- 98% history quality

This is a controlled demo-rehearsal candidate, not a live or production
promotion. The default preset is shadow-only. The ordering template requires an
explicit second switch and the EA hard-rejects non-demo accounts.
