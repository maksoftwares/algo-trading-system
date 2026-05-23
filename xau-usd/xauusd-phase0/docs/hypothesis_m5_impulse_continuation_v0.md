# M5 Impulse Continuation v0 Hypothesis

Hypothesis date: 2026-05-23
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 250-1200
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 40%-60%
Expected worst single month: -10R to -30R
Expected max consecutive zero months: 1
Expected R-multiple distribution: Many small failed continuation losses near -1R, fewer +1.5R momentum extensions, and no acceptable pass if one broker or cost model carries the result.

## Mechanical Definition

This candidate is a bidirectional XAUUSD M5 impulse-continuation expert. It tests whether two consecutive directional M5 candles in the H1 trend direction create enough short-term follow-through to survive Phase 0 costs. It is not a breakout-retest, swing-breakout-retest, pivot reclaim, VWAP reclaim, inside-bar breakout, compression, or liquidity-sweep reversal strategy.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries and H1 trend context.
2. Eligible trigger window: completed M5 bars whose bar start is from 07:00 UTC through 16:55 UTC.
3. Long trend context: H1 close must be above H1 EMA50, and H1 EMA50 slope over 12 H1 bars must be non-negative.
4. Short trend context: H1 close must be below H1 EMA50, and H1 EMA50 slope over 12 H1 bars must be non-positive.
5. Long impulse: the previous and current completed M5 candles must both close bullish, the current close must exceed the previous close, the current candle must close in the upper 30% of its range, the current body must be at least 45% of range, and the previous body must be at least 35% of range.
6. Short impulse: the previous and current completed M5 candles must both close bearish, the current close must be below the previous close, the current candle must close in the lower 30% of its range, the current body must be at least 45% of range, and the previous body must be at least 35% of range.
7. Net move: the two-candle net move from previous open to current close must be at least 0.75 times current M5 ATR(14).
8. Exhaustion guard: the two-candle high-low range must not exceed 3.0 times current M5 ATR(14).
9. Entry: enter at the next eligible M5 open after the impulse candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
10. Stop: for longs, place the stop below the two-candle impulse low by 0.20 times M5 ATR(14). For shorts, place the stop above the two-candle impulse high by 0.20 times M5 ATR(14).
11. Target: use a fixed 1.5R target.
12. Cooldown: take at most one signal in the same direction every 12 M5 bars.
13. Invalidation: no setup if ATR, H1 trend features, candle quality, or stop/target construction is unavailable or creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is moderate-to-high frequency. Opportunities should appear when short-term directional pressure aligns with the H1 trend and is not already an oversized exhaustion candle. It should fail when the two-bar impulse is absorbed immediately, when cost consumes the follow-through, or when the H1 trend context is too coarse to filter chop.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer should be plausible because short-term impulse continuation is not XAU-only, though XAUUSD may remain the strongest expression.

## Why This Hypothesis Should Exist

Two consecutive high-quality M5 candles in the H1 trend direction can represent short-term order-flow pressure. If that impulse is large enough to matter but not so large that it is already exhausted, immediate follow-through may produce a repeatable 1.5R continuation edge. This candidate tests direct momentum follow-through without waiting for a retest.

This candidate is independent from the approved breakout-retest family because it does not depend on a structural level, retest, hold, pivot, or prior range. It asks whether raw M5 impulse plus H1 trend context is sufficient.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Manual adversarial review finds logic gaps above the allowed threshold.
- The strategy only passes after adding discretionary session, news, trend, volatility, or candle filters after results are known.

Code mapping after implementation:

- M5/H1 feature construction: `src/phase0/strategies/m5_impulse_continuation_v0.py::M5ImpulseContinuationV0Strategy.prepare_features`
- M5 impulse trigger: `src/phase0/strategies/m5_impulse_continuation_v0.py::M5ImpulseContinuationV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/m5_impulse_continuation_v0.py::M5ImpulseContinuationV0Strategy.build_trade_plan`
