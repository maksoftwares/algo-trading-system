# Extreme Activity Mean Reversion v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 40-220
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-60%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many failed fades near -1R, fewer 1.5R snapback wins, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a bidirectional XAUUSD extreme-activity mean-reversion expert. It tests whether a very large M5 candle that sweeps a recent high or low and closes back inside the prior range has enough snapback edge to survive Phase 0 costs and concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries.
2. Recent range reference: use the prior 96 completed M5 highs and lows, excluding the trigger candle.
3. Extreme activity gate: the trigger M5 candle high-low range must be at least 2.2 times current M5 ATR(14).
4. Failed upside spike short: the trigger candle must trade at least 0.35 times current M5 ATR(14) above the prior 96-bar high, then close at least 0.10 times current M5 ATR(14) below that prior high.
5. Upside rejection candle: the failed-upside trigger candle must close bearish, close in the lower 40% of its high-low range, and have body at least 25% of its high-low range.
6. Failed downside spike long: the trigger candle must trade at least 0.35 times current M5 ATR(14) below the prior 96-bar low, then close at least 0.10 times current M5 ATR(14) above that prior low.
7. Downside rejection candle: the failed-downside trigger candle must close bullish, close in the upper 40% of its high-low range, and have body at least 25% of its high-low range.
8. Entry: enter at the next eligible M5 open after the failed spike candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
9. Stop: for shorts, stop above the spike high by 0.25 times current M5 ATR(14); for longs, stop below the spike low by 0.25 times current M5 ATR(14).
10. Target: use a fixed 1.5R target.
11. Cooldown: ignore additional signals for 24 M5 bars after a generated signal.
12. Invalidation: no setup if ATR, prior range, or rejection candle requirements are unavailable.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/extreme_activity_mean_reversion_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is moderate frequency. The candidate should cluster around sharp liquidation or stop-run candles and should lose when the extreme candle is the beginning of a genuine directional repricing event.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, or a clear rejection if frequency is too low.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

Gold often produces abrupt liquidation candles and stop sweeps. Some extreme candles exhaust when they fail to close outside the recent range, especially when the move was liquidity-seeking rather than information-driven. This candidate isolates that behavior using only completed M5 bars and prior-range references.

This candidate is intentionally different from `post_spike_short_v0`. It is bidirectional, requires the entire trigger candle to be extreme relative to ATR, and requires a failed close back inside the recent 96-bar range.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Manual adversarial review finds logic gaps above the allowed threshold.
- The strategy only passes after adding discretionary time, news, volatility, or price-action filters after results are known.

Code mapping:

- Extreme range and prior-range feature construction: `src/phase0/strategies/extreme_activity_mean_reversion_v0.py::prepare_features`
- Failed spike trigger: `src/phase0/strategies/extreme_activity_mean_reversion_v0.py::_setup_at_position`
- Stop/target construction: `src/phase0/strategies/extreme_activity_mean_reversion_v0.py::build_trade_plan`
