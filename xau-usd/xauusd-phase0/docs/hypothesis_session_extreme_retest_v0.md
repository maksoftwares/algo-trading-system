# Session Extreme Retest v0 Hypothesis

Hypothesis date: 2026-05-23
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 600-2,500
Expected cost-adjusted PF: 1.15-1.50
Expected losing-month percentage: 35%-55%
Expected worst single month: -8R to -22R
Expected max consecutive zero months: 1
Expected R-multiple distribution: many small failed retests near -1R, fewer +1.5R continuation wins, and no acceptable pass if one broker, month, or tiny trade cluster explains the result.

## Mechanical Definition

This candidate is a bidirectional XAUUSD session-extreme retest expert. It tests whether breaks of completed Asia or London session highs/lows that retest and hold continue far enough to survive Phase 0 costs. It is same-family with breakout/retest mechanics, but it uses session extremes only and does not use daily, weekly, swing, or round-number levels.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries and M5 trigger/retest/confirmation candles.
2. Session levels: completed Asia high/low and completed London high/low.
3. Asia session for v0: completed M5 bars whose bar start time is from 00:00 UTC through 05:55 UTC.
4. London session for v0: completed M5 bars whose bar start time is from 07:00 UTC through 10:55 UTC.
5. Asia levels are eligible only after 07:00 UTC. London levels are eligible only after 13:30 UTC.
6. Long setup: an M5 candle must close at least 0.30 times ATR(14) above an eligible session high. Within the next 20 completed M5 bars, a retest candle must trade back to the level plus 5 points or closer and close at or above the level. A bullish confirmation candle after the retest must trigger a buy-stop entry one point above the retest high.
7. Short setup: an M5 candle must close at least 0.30 times ATR(14) below an eligible session low. Within the next 20 completed M5 bars, a retest candle must trade back to the level minus 5 points or closer and close at or below the level. A bearish confirmation candle after the retest must trigger a sell-stop entry one point below the retest low.
8. Stop: use the inherited breakout-retest stop rule, with long stops below the retest low by 0.10 ATR(14) and short stops above the retest high by 0.10 ATR(14).
9. Target: use a fixed 1.5R target.
10. Order expiry: pending stop entries expire after 5 M5 bars.
11. Invalidation: no setup if ATR is unavailable, the level is not complete, the retest closes through the level, stop/entry construction creates non-positive risk, or the pending entry does not trigger before expiry.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is high enough frequency for 9-cell matrix testing. Opportunities should cluster after London and New York participants interact with completed Asia/London extremes. It should lose when the session break is false, when the retest does not attract continuation flow, or when the session extreme is too obvious and cost-sensitive.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer should be plausible because session-extreme retests are not XAU-only mechanics, though XAUUSD may remain the strongest expression.

## Why This Hypothesis Should Exist

Completed Asia and London highs/lows are visible intraday liquidity references. If price breaks one of these levels, returns to it, and holds, the level can act as a short-term acceptance boundary. That behavior is related to breakout/retest logic, but the level source is session structure rather than swing, daily, weekly, or round-number structure.

This candidate should not be counted as true diversification from `breakout_retest`; it is a same-family retest variant. Its value is to test whether there is a second deployable expression of the accepted retest edge while independent-family research continues.

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

- Session-level feature construction: `src/phase0/strategies/session_extreme_retest_v0.py::SessionExtremeRetestV0Strategy.prepare_features`
- Session-level candidate selection: `src/phase0/strategies/session_extreme_retest_v0.py::SessionExtremeRetestV0Strategy._candidate_levels_from_arrays`
- Retest trigger and stop/target construction: inherited from `src/phase0/strategies/breakout_retest.py::BreakoutRetestStrategy`
