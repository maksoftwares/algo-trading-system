# Daily Pivot Reclaim v0 Hypothesis

Hypothesis date: 2026-05-23
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 120-500
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 40%-60%
Expected worst single month: -8R to -22R
Expected max consecutive zero months: 1
Expected R-multiple distribution: Many valid failed reclaims near -1R, fewer +1.5R winners, and no acceptable pass if a small number of trades or months dominate the result.

## Mechanical Definition

This candidate is a bidirectional XAUUSD previous-day pivot reclaim expert. It tests whether completed M5 candles that trade through the prior UTC day's classic HLC pivot and close back through it have enough short-term auction-reversion edge to survive Phase 0 costs. It is not a breakout-retest, trend-pullback, session-range breakout, liquidity-sweep high/low, VWAP, or compression strategy.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries and M5 trigger candles.
2. Previous-day pivot: for each UTC day, compute the prior UTC day's classic pivot as `(previous_day_high + previous_day_low + previous_day_close) / 3`.
3. Eligible trigger window: completed M5 bars whose bar start time is from 07:00 UTC through 16:55 UTC.
4. Bullish reclaim: a completed M5 candle must trade at least 0.25 times current M5 ATR(14) below the previous-day pivot and close at least 0.10 times current M5 ATR(14) above the pivot. The candle must close bullish, close in the upper 40% of its high-low range, and have body at least 25% of its range.
5. Bearish reclaim: a completed M5 candle must trade at least 0.25 times current M5 ATR(14) above the previous-day pivot and close at least 0.10 times current M5 ATR(14) below the pivot. The candle must close bearish, close in the lower 40% of its high-low range, and have body at least 25% of its range.
6. Entry: enter at the next eligible M5 open after the reclaim candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
7. Stop: for long setups, place the stop below the reclaim candle low by 0.25 times M5 ATR(14). For short setups, place the stop above the reclaim candle high by 0.25 times M5 ATR(14).
8. Target: use a fixed 1.5R target.
9. Frequency control: take at most one setup per UTC day per direction.
10. Invalidation: no setup if prior-day pivot is unavailable, the trigger candle is outside the allowed window, ATR is unavailable, candle quality fails, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is moderate frequency. Opportunities should cluster when the market crosses the prior-day pivot and immediately re-accepts on the other side. It should lose when the pivot cross is the beginning of genuine directional repricing.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer should be plausible because previous-day pivot auction behavior is not XAU-only, though XAUUSD may remain the strongest expression.

## Why This Hypothesis Should Exist

The previous-day classic pivot is a simple prior-session auction reference. A completed candle that rejects one side of the pivot and closes decisively back through it may show failed directional acceptance around that reference, creating short-term mean-reversion pressure. The rule uses only prior-day information and the completed trigger candle.

This candidate is independent from `breakout_retest` and `swing_breakout_retest_v0`, which both require continuation after a break and retest. It is also distinct from `liquidity_sweep_reversal_v0`, which used visible highs/lows rather than a previous-day HLC pivot.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Manual adversarial review finds logic gaps above the allowed threshold.
- The strategy only passes after adding discretionary time, news, trend, volatility, or candle filters after results are known.

Code mapping after implementation:

- Previous-day pivot feature construction: `src/phase0/strategies/daily_pivot_reclaim_v0.py::DailyPivotReclaimV0Strategy.prepare_features`
- Pivot reclaim trigger: `src/phase0/strategies/daily_pivot_reclaim_v0.py::DailyPivotReclaimV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/daily_pivot_reclaim_v0.py::DailyPivotReclaimV0Strategy.build_trade_plan`
