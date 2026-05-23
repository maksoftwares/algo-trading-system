# M15 Inside-Bar Breakout v0 Hypothesis

Hypothesis date: 2026-05-23
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 150-700
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 40%-60%
Expected worst single month: -8R to -25R
Expected max consecutive zero months: 1
Expected R-multiple distribution: Frequent -1R failures, fewer +1.5R trend-expansion wins, and no acceptable pass if one broker/cost cell dominates the edge.

## Mechanical Definition

This candidate is a bidirectional XAUUSD M15 inside-bar breakout expert. It tests whether a completed M15 inside bar after a wider mother candle contains enough compressed auction energy that a confirmed M5 break in the H1 trend direction survives Phase 0 costs. It is not a breakout-retest, swing-breakout-retest, previous-day high/low retest, pivot reclaim, VWAP reclaim, or liquidity-sweep reversal strategy.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M15 setup bars, M5 trigger bars, and H1 trend context.
2. Mother bar: the previous completed M15 candle is the mother candle.
3. Inside bar: the current completed M15 candle must have high less than or equal to the mother high and low greater than or equal to the mother low.
4. Compression: the inside-bar range must be no more than 70% of the mother range.
5. Valid mother range: the mother range must be at least 0.60 times the prior M15 ATR(14).
6. Eligible trigger window: completed M5 bars whose bar start is from 07:00 UTC through 16:55 UTC.
7. Trigger age: the M5 breakout must happen no more than 45 minutes after the inside M15 candle closes.
8. Long breakout: a completed M5 candle must close at least 0.10 times current M5 ATR(14) above the mother high, close bullish, close in the upper 35% of its range, have body at least 40% of its range, and H1 close must be above H1 EMA50 with non-negative EMA50 slope over 12 H1 bars.
9. Short breakout: a completed M5 candle must close at least 0.10 times current M5 ATR(14) below the mother low, close bearish, close in the lower 35% of its range, have body at least 40% of its range, and H1 close must be below H1 EMA50 with non-positive EMA50 slope over 12 H1 bars.
10. Entry: enter at the next eligible M5 open after the trigger candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
11. Stop: for long setups, place the stop at the lower of the inside-bar low and one M5 ATR below estimated entry. For short setups, place the stop at the higher of the inside-bar high and one M5 ATR above estimated entry.
12. Target: use a fixed 1.5R target.
13. Frequency control: take at most one setup per inside bar per direction.
14. Invalidation: no setup if any required timeframe, ATR, EMA, inside-bar, trigger, or stop/target value is unavailable or creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is moderate frequency. Opportunities should appear when a completed M15 inside bar compresses after a directional mother candle and a follow-through M5 candle breaks the mother range in the H1 trend direction. It should fail when the inside bar becomes chop, when the mother range is a one-bar exhaustion, or when cost consumes a thin continuation edge.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer should be plausible because inside-bar expansion is not XAU-only, though XAUUSD may remain the strongest expression.

## Why This Hypothesis Should Exist

Inside bars are simple completed-candle compression structures. If the market compresses after a meaningful M15 mother candle, then breaks the mother range with a decisive M5 close in the H1 trend direction, a short-term volatility-release move may follow. This candidate tests direct expansion without a retest or failed-break reversal requirement.

This candidate is independent from the approved breakout-retest family because it does not require a level break, retest, hold, or continuation sequence. It is also distinct from previous rejected compression candidates because the setup definition is a completed M15 inside-bar structure rather than rolling range compression.

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

- Inside-bar feature construction: `src/phase0/strategies/m15_inside_bar_breakout_v0.py::M15InsideBarBreakoutV0Strategy.prepare_features`
- M5 breakout trigger: `src/phase0/strategies/m15_inside_bar_breakout_v0.py::M15InsideBarBreakoutV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/m15_inside_bar_breakout_v0.py::M15InsideBarBreakoutV0Strategy.build_trade_plan`
