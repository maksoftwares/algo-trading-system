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

## Frequency V2 result

The original 62-trade strategy remains frozen as the H4-chop control. The
frequency campaign tested 1,260 bar-pattern candidates, 1,920 scheduled
candidates, and 3,072 asymmetric scheduled candidates before freezing and
opening their next stages. The strict twelve-specialist portfolio passed
2022-2024 validation but failed the 2024-2026 adaptive exam and was rejected.

The controlled-demo fallback combines:

- an M15 RSI-extreme long frequency core at 0.01 lots;
- an additional 0.01 lots only in completed-H4 `trend_up` or `trend_down`;
- the unchanged H4-chop Asia/London short control at 0.01 lots.

Capital.com real-tick evidence for 2024-07 through 2026-07:

- 697 trades over 615 active broker dates (1.133/day);
- 57.82% win rate;
- 1.3075 portfolio profit factor;
- +$119.42 at the declared lots;
- $28.45 maximum closed-trade drawdown (0.285% of $10,000);
- 64% positive months;
- 1.019 PF after removing the best 5% of trades;
- maximum two concurrent positions.

This passes the adaptive 1.30 controlled-demo floor but remains below the 1.45
control target. It does not pass the original strict regime-portfolio contract.
The period is adaptive research, not an untouched holdout.
Start with the fail-closed shadow presets and follow `FREQUENCY_V2_DEMO.md`.

Rebuild the packaged MT5 portfolio evidence with:

```powershell
python build_frequency_v2_mt5_evidence.py
```
