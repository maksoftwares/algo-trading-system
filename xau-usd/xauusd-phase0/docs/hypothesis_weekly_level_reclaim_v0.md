# Weekly Level Reclaim v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 20-120
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-65%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many failed reclaims near -1R, fewer 1.5R reclaim wins, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a bidirectional XAUUSD weekly-level reclaim expert. It tests whether failed sweeps through the previous ISO week's high or low have enough mean-reversion edge to survive Phase 0 costs and concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries.
2. Week definition: use ISO week/year from the M5 bar-start timestamp in UTC.
3. Level source: compute each ISO week's high and low from completed M5 bars. For the current ISO week, use the immediately prior ISO week's high and low.
4. Long reclaim: the trigger M5 candle must trade at least 0.35 times current M5 ATR(14) below the previous-week low, then close at least 0.10 times current M5 ATR(14) back above the previous-week low.
5. Long reclaim candle: the trigger candle must close bullish, close in the upper 40% of its high-low range, and have body at least 30% of its high-low range.
6. Short reclaim: the trigger M5 candle must trade at least 0.35 times current M5 ATR(14) above the previous-week high, then close at least 0.10 times current M5 ATR(14) back below the previous-week high.
7. Short reclaim candle: the trigger candle must close bearish, close in the lower 40% of its high-low range, and have body at least 30% of its high-low range.
8. Entry: enter at the next eligible M5 open after the reclaim candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
9. Stop: for longs, stop below the sweep low by 0.25 times current M5 ATR(14); for shorts, stop above the sweep high by 0.25 times current M5 ATR(14).
10. Target: use a fixed 1.5R target.
11. Weekly duplicate rule: allow at most one long and one short setup per ISO week.
12. Invalidation: no setup if previous-week levels, ATR, or reclaim candle requirements are unavailable.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/weekly_level_reclaim_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is lower frequency than intraday session candidates. The candidate should cluster around failed auctions through widely visible weekly extremes and should lose when a weekly break becomes genuine continuation.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, or a clear rejection if frequency is too low.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

Weekly highs and lows are slow, visible liquidity references. A quick sweep and reclaim can indicate failed acceptance outside the weekly range rather than a sustained breakout. This candidate tests that behavior with a single objective level source and completed M5 reclaim candles.

This candidate is intentionally different from the prior-day retest candidate. It tests failed sweeps and reclaims of slower weekly levels, not continuation after a daily-level break and retest.

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

- Previous-week level construction: `src/phase0/strategies/weekly_level_reclaim_v0.py::prepare_features`
- Reclaim trigger: `src/phase0/strategies/weekly_level_reclaim_v0.py::_setup_at_position`
- Stop/target construction: `src/phase0/strategies/weekly_level_reclaim_v0.py::build_trade_plan`
