# A1 XAU M5 Daily Extreme Reclaim Preregistration

Date: 2026-07-05

Status: PREREGISTERED BEFORE EXACT-MT5 RUN

## Objective

Test one genuinely separate gold entry family after the H4 D1-compression clue failed pre-2022 robustness: M5 mean reversion after the current broker day has stretched far enough from the day open and the latest completed M5 bar reclaims away from the day high/low.

This is not a retune of the D1-compression/H4-expansion clue. It uses a different mechanism: intraday exhaustion and reclaim.

## Causal Rule

- Compute current broker-day open/high/low by scanning completed M5 bars from 00:00 broker time through the completed signal bar.
- Use previous completed D1 ATR only.
- Short setup: current day has moved up by at least `InpDailyExtremeMinMoveAtr * prior_D1_ATR`, the signal bar is near the causal day high, and closes back below that high by `InpDailyExtremeReclaimAtr * prior_D1_ATR`.
- Long setup: symmetric rule after a downside day stretch.
- Entry is handled by the existing executor after the completed M5 decision.
- Stop is beyond the causal day extreme by `InpDailyExtremeStopBufferAtr * prior_D1_ATR`.
- Initial target is `2.00R`.

## Design Window

Run these six variants on exact MT5 Strategy Tester only:

- Symbol: XAUUSD
- Timeframe: M5
- Design period: 2016.01.01 through 2021.12.31
- Tester root: `C:\MT5A1M5MomentumBacktest`
- Currency: USD
- Lot model: unchanged fixed 0.01 lot, plus manual signal-shape metrics.

| Variant | Session | Min Move D1 ATR | Touch D1 ATR | Reclaim D1 ATR | Stop Buffer D1 ATR | M5 Range ATR | Body | Close Loc |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `der_broad_all_day_075` | 0-24 | 0.75 | 0.08 | 0.08 | 0.08 | 0.15 | 0.20 | 0.55/0.45 |
| `der_broad_liquid_075` | 7-22 | 0.75 | 0.08 | 0.08 | 0.08 | 0.15 | 0.20 | 0.55/0.45 |
| `der_standard_liquid_100` | 7-22 | 1.00 | 0.06 | 0.10 | 0.10 | 0.20 | 0.25 | 0.58/0.42 |
| `der_us_100` | 12-23 | 1.00 | 0.06 | 0.10 | 0.10 | 0.20 | 0.25 | 0.58/0.42 |
| `der_deep_reclaim_100` | 7-22 | 1.00 | 0.08 | 0.15 | 0.08 | 0.15 | 0.20 | 0.55/0.45 |
| `der_exhaustion_125` | 7-22 | 1.25 | 0.06 | 0.10 | 0.10 | 0.20 | 0.25 | 0.58/0.42 |

Common inputs:

- `InpSignalMode=11`
- `InpRiskReward=2.00`
- `InpMaxTradesPerDay=24`
- `InpCooldownMinutes=0`
- `InpOnePositionPerMagic=false`
- `InpMaxOpenPositionsPerMagic=16`
- `InpStopCeilingPoints=0`
- `InpMaxEstimatedCostR=0.15`
- `InpDailyExtremeMinBarsSinceOpen=24`

## Selection Rule

After the design run:

1. Design core pass means `trades >= 100`, `win_rate_pct >= 50.0`, `avg_win_loss_ratio >= 2.0`, `profit_factor > 1.0`, and positive manual P&L.
2. Design near-frontier means `trades >= 100`, `win_rate_pct >= 48.0`, `avg_win_loss_ratio >= 1.80`, `profit_factor >= 1.20`, and positive manual P&L.
3. If no variant reaches core pass or near-frontier, kill the family without spending a 2022-2026 exam.
4. If one or more variants qualify, freeze at most three variants before the exam. Sort by core pass first, then manual P&L, then active-day percentage, then trade count.
5. Run the frozen variants exactly once on 2022.01.01 through 2026.06.30.

## Promotion Rule

Any exam winner is still `WATCHLIST_ONLY`, not demo-ready. Demo discussion requires exact-MT5 exam core pass, robustness work, owner approval, and external review.

Spend the reviewer only if the exam produces a genuine contender or a very close miss where direction/next-step judgment is valuable.
