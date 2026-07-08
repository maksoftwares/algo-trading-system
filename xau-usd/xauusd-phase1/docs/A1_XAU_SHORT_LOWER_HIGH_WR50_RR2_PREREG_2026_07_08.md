# A1 XAU Lower-High Short WR50 RR2 Preregistration

Generated: 2026-07-08

## Goal

Test a new purpose-built short signal class for the hard target:

- WR >= 50%.
- Fixed `InpRiskReward=2.00`.
- W/L near 2.0 after real MT5 exits.
- At least 100 trades over `2022.07.01 -> 2026.06.30`.

## Signal Class

`SIGNAL_BEAR_LOWER_HIGH_REJECTION = 17`

The signal fires only when:

- Current completed M5 bar is bearish.
- Current completed M5 bar closes near its low.
- Recent pullback high stays below a prior swing high by a fixed ATR gap.
- There was a prior drop from the earlier swing high.
- Pullback reaches the M5 EMA zone.
- Current completed M5 close rejects back below the M5 EMA zone.

All variants use:

- Direction: short only.
- D1 structural down gate.
- H1/H4 downtrend filters.
- No hour/session/day/month masks.
- Fixed RR2, no trailing/breakeven/partial exits.

## Variants

| Variant | Purpose |
| --- | --- |
| `lower_high_lh1_base` | Base lower-high rejection definition |
| `lower_high_lh2_deeper_drop` | Requires deeper prior drop and larger lower-high gap |
| `lower_high_lh3_tighter_reject` | Requires tighter close/rejection quality |

## Pass Gate

- WR >= 50%.
- W/L >= 1.90.
- Trades >= 100.
- Net > 0.
- Cost-stress net after subtracting `0.30` per trade > 0.
- Cost-stress PF >= 1.15.
- 2023+2024 combined net >= 0.
- Net after top 10 winning trades removed remains > 0.
- Net after top 3 entry days removed remains > 0.

If no variant passes, do not keep tightening thresholds from the failed outputs. The next design step must be conceptually new or reviewed first.
