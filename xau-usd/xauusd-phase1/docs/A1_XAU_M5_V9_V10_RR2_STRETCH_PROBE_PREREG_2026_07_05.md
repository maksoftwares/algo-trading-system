# A1 XAU M5 V9/V10 RR2 Stretch Probe Preregistration

Generated UTC: `2026-07-05T06:48:00Z`

## Purpose

The owner goal requires signal-level win rate `>=50%`, realized average winning trade / average losing trade `>=2.0`, and near-daily activity. The confirmed RR2 long-only book has payoff but not hit rate, while the previously exact-MT5-tested V9/V10 distinct families have frequency and hit rate at small targets (`0.6R`) but insufficient payoff.

This probe tests the narrow question: do the best high-frequency/high-hit-rate V9/V10 mechanisms retain enough win rate when stretched to `2.0R`?

## Boundary

- Exact MT5 Strategy Tester only, isolated root `C:\MT5A1M5MomentumBacktest`.
- No live/demo runtime terminal, chart, preset, order, position, or broker state may be changed.
- No optimizer.
- No post-hoc threshold search.
- No reviewer token unless a row reaches at least the core owner shape: WR `>=50%` and realized W/L `>=2.0`.

## Window

- Symbol/timeframe: `XAUUSD`, `M5`
- Period: `2022.07.01 -> 2026.06.30`
- Account context: `1025742 / Capital.ComMena-Demo`
- Tester model: every tick, local agent only
- Deposit/currency: `1000 USD`

## Frozen Variants

All variants preserve their previously tested mechanism parameters and change only `InpRiskReward` from the small-target family to `2.00`.

| Variant | Mechanism | Direction/filter | Frozen change |
| --- | --- | --- | --- |
| `v9_sweep_h1_long_rr2p0` | M5 sweep-reclaim | H1 trend, long-only | `InpRiskReward=2.00` |
| `v9_sweep_h1h4_long_rr2p0_v4mask` | M5 sweep-reclaim | H1+H4 trend, long-only, V4 weak-hour mask | `InpRiskReward=2.00` |
| `v10_or_london_h1h4_both_rr2p0` | London opening-range continuation | H1+H4 trend, both directions | `InpRiskReward=2.00` |
| `v10_or_asia_h1h4_long_rr2p0` | Asia opening-range continuation | H1+H4 trend, long-only | `InpRiskReward=2.00` |

## Pass/Fail Read

For each row report:

- trades
- signal-level win rate
- realized average win / average loss
- active entry days and active-day percent
- manual P&L from parsed trade CSV
- PF
- maximum closed drawdown
- last-12-month standalone stats

Verdict rules:

- `OWNER_GOAL_HIT_REVIEW_REQUIRED`: WR `>=50%`, realized W/L `>=2.0`, active-day percent `>=90%`.
- `CORE_SHAPE_HIT_FREQUENCY_GAP`: WR `>=50%`, realized W/L `>=2.0`, active-day percent `<90%`.
- `NEAR_MISS`: WR `>=48%`, realized W/L `>=1.9`.
- `REJECT_NO_OWNER_GOAL_HIT`: no row reaches the core owner shape.

## Expected Use

If no row reaches core shape, do not keep stretching/tuning these same V9/V10 mechanisms. Pivot to a genuinely different high-hit-rate entry family or a design-window-only discovery pass.
