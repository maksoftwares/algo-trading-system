# Liquidity Sweep Reversal v0 Hypothesis

Hypothesis date: 2026-05-23
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 180-650
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 40%-60%
Expected worst single month: -10R to -24R
Expected max consecutive zero months: 1
Expected R-multiple distribution: Many valid failed sweeps near -1R, fewer +1.5R winners, and no acceptable pass if one symbol, month, or small trade cluster explains the result.

## Mechanical Definition

This candidate is a bidirectional XAUUSD liquidity-sweep reversal expert. It tests whether completed M5 stop sweeps through visible session or prior-day extremes that immediately close back inside the level have enough reversal edge to survive Phase 0 costs. It is not a breakout, retest, continuation, trend-pullback, or range-mean-reversion strategy.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries, M5 trigger candles, and M15 ATR context.
2. Visible high-side liquidity pools: previous UTC day high, completed Asia-session high, and completed London-session high.
3. Visible low-side liquidity pools: previous UTC day low, completed Asia-session low, and completed London-session low.
4. Asia session for v0: completed M5 bars whose bar start time is from 00:00 UTC through 05:55 UTC.
5. London session for v0: completed M5 bars whose bar start time is from 07:00 UTC through 10:55 UTC.
6. Eligible trigger window: completed M5 bars whose bar start time is from 07:00 UTC through 16:55 UTC.
7. Asia levels are eligible only after 07:00 UTC. London levels are eligible only after 13:30 UTC. Prior-day levels are eligible throughout the trigger window.
8. Bearish sweep reversal: a completed M5 candle must trade at least 0.20 times current M5 ATR(14) above a high-side liquidity level and close at least 0.05 times current M5 ATR(14) back below that level. The candle must close bearish, close in the lower 45% of its high-low range, have body at least 20% of its range, and have an upper wick at least 1.25 times its body.
9. Bullish sweep reversal: a completed M5 candle must trade at least 0.20 times current M5 ATR(14) below a low-side liquidity level and close at least 0.05 times current M5 ATR(14) back above that level. The candle must close bullish, close in the upper 45% of its high-low range, have body at least 20% of its range, and have a lower wick at least 1.25 times its body.
10. Entry: enter at the next eligible M5 open after the sweep-reversal candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
11. Stop: for short setups, place the stop above the sweep high by 0.25 times M5 ATR(14). For long setups, place the stop below the sweep low by 0.25 times M5 ATR(14).
12. Target: use a fixed 1.5R target.
13. Frequency control: take at most one setup per UTC day, direction, and liquidity-level kind.
14. Invalidation: no setup if the trigger candle is outside the allowed window, the level is not yet complete, ATR values are unavailable, candle quality fails, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is moderate frequency. Opportunities should cluster around London and New York liquidity discovery after a visible high or low is swept and rejected. It should lose when the sweep becomes genuine trend continuation or when the rejection candle is only noise.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer should be plausible because stop-sweep reversal is a cross-market liquidity behavior, though XAUUSD may remain the strongest expression.

## Why This Hypothesis Should Exist

Gold often trades through visible prior highs/lows and session extremes to source liquidity. Some sweeps fail immediately when the move is liquidity-taking rather than real acceptance outside the level. A completed candle that both sweeps the level and closes back inside can mark trapped breakout participation and short-term reversal pressure.

This candidate is independent from `breakout_retest` and `swing_breakout_retest_v0`, which both require continuation after a break and retest. This candidate trades immediate failed acceptance back inside a swept level.

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

- Liquidity-level feature construction: `src/phase0/strategies/liquidity_sweep_reversal_v0.py::LiquiditySweepReversalV0Strategy.prepare_features`
- Sweep-reversal trigger: `src/phase0/strategies/liquidity_sweep_reversal_v0.py::LiquiditySweepReversalV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/liquidity_sweep_reversal_v0.py::LiquiditySweepReversalV0Strategy.build_trade_plan`
