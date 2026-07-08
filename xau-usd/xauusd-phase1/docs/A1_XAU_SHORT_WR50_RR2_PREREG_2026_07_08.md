# A1 XAU Short WR50 RR2 Preregistration

Generated: 2026-07-08

## Goal

Build or reject a standalone XAUUSD short expert candidate with:

- Win rate at least 50%.
- Fixed RR approximately 2.0.
- Understandable trade frequency, defined for this pass as at least 100 trades over `2022.07.01 -> 2026.06.30`.
- Exact MT5 Strategy Tester evidence only.

This pass does not tune by hour, session, weekday, month, or recent quarter. It tests a small fixed set of structural short-entry shapes before seeing results.

## Execution Contract

- Terminal: `C:\MT5A1M5MomentumBacktest`
- Symbol/timeframe: `XAUUSD` / `M5`
- Direction: short only
- Window: `2022.07.01 -> 2026.06.30`
- Deposit/currency: `1000 USD`
- Lot: fixed `0.01`
- RR: `InpRiskReward=2.00`
- Max spread: `75`
- Max estimated cost R: `0.05`
- Max trades per day: `24`
- Cooldown: `0`
- No hour/session/day/month block lists

## Variants

All variants are preregistered and report every result.

| Variant | Signal idea | Regime/filter intent |
| --- | --- | --- |
| `wr50_s1_m5_sweep_structural` | M5 local high sweep/reclaim short | structural D1 down + H1/H4 downtrend |
| `wr50_s2_prior_day_sweep_structural` | prior-day-high sweep/reclaim short | structural D1 down + H1/H4 downtrend |
| `wr50_s3_ema_pullback_structural` | M5 EMA pullback continuation short | structural D1 down + H1/H4 downtrend |
| `wr50_s4_m5_ema_trend_structural` | M5 EMA trend continuation short | structural D1 down + H1/H4 downtrend |
| `wr50_s5_v2_strict_retest_structural` | stricter V2 breakdown-retest short | structural D1 down + H1/H4 downtrend |

## Pass Gate

A variant can become a standalone review candidate only if all checks pass:

- WR >= 50.00%.
- Average win/loss >= 1.90, while using fixed `InpRiskReward=2.00`.
- Trades >= 100.
- Full-window net > 0.
- Cost-stress net after subtracting `0.30` per trade > 0.
- Cost-stress PF >= 1.15.
- 2023+2024 combined net >= 0.
- Net remains > 0 after removing top 10 winning trades.
- Net remains > 0 after removing top 3 entry days.

If no variant passes, the result is not a failure of execution; it means the 50% WR / 2R standalone short target needs a new signal implementation rather than more filtering of existing signals.

## Forbidden

- No parameter grid or post-result threshold selection.
- No hour/session/day/month masking.
- No changing RR below 2.0 to lift WR.
- No break-even, trailing, or partial-exit changes.
- No demo/forward-watchlist claim without reviewer sign-off.
