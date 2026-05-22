# Previous Day Extreme Retest v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 40-180
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-60%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many failed retests near -1R, fewer 1.5R continuation wins, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a bidirectional XAUUSD previous-day extreme retest expert. It tests whether a break and retest of the prior UTC day's high or low has enough continuation edge to survive Phase 0 costs and concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries.
2. Level source: compute each UTC day's high and low from completed M5 bars. For the current UTC date, use the immediately prior available UTC day's high and low.
3. Long breakout: within the 18 M5 bars before confirmation, a completed M5 candle must close at least 0.25 times current M5 ATR(14) above the previous-day high and close bullish.
4. Long retest: after the long breakout and before confirmation, a completed M5 candle must trade back to within 0.15 times current M5 ATR(14) above the previous-day high and close no more than 0.10 times current M5 ATR(14) below the previous-day high.
5. Long confirmation: the current completed M5 candle must close bullish, close at least 0.10 times current M5 ATR(14) above the previous-day high, close in the upper 40% of its range, and have body at least 30% of its range.
6. Short breakout: within the 18 M5 bars before confirmation, a completed M5 candle must close at least 0.25 times current M5 ATR(14) below the previous-day low and close bearish.
7. Short retest: after the short breakout and before confirmation, a completed M5 candle must trade back to within 0.15 times current M5 ATR(14) below the previous-day low and close no more than 0.10 times current M5 ATR(14) above the previous-day low.
8. Short confirmation: the current completed M5 candle must close bearish, close at least 0.10 times current M5 ATR(14) below the previous-day low, close in the lower 40% of its range, and have body at least 30% of its range.
9. Entry: enter at the next eligible M5 open after the confirmation candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
10. Stop: for longs, stop below the lesser of the level or retest low by 0.25 times current M5 ATR(14); for shorts, stop above the greater of the level or retest high by 0.25 times current M5 ATR(14).
11. Target: use a fixed 1.5R target.
12. Daily duplicate rule: allow at most one long and one short setup per UTC date.
13. Invalidation: no setup if prior-day levels, ATR, breakout, retest, or confirmation requirements are unavailable.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/previous_day_extreme_retest_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is moderate frequency. The candidate should cluster around prior-day high/low breaks that come back to hold the level. It should lose when the first break is a false auction or when the retest hold fails.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, or a clear rejection if frequency is too low.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

Prior-day highs and lows are common liquidity reference points. A break that later retests and holds the level may represent a successful auction transition from resistance to support or support to resistance. This candidate isolates that behavior with one objective level source and a fixed M5 sequence window.

This candidate is intentionally narrower than `breakout_retest`. It only uses prior-day extremes and does not include weekly levels, daily levels from other sessions, or swing levels.

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

- Prior-day level construction: `src/phase0/strategies/previous_day_extreme_retest_v0.py::prepare_features`
- Break/retest/confirmation trigger: `src/phase0/strategies/previous_day_extreme_retest_v0.py::_setup_at_position`
- Stop/target construction: `src/phase0/strategies/previous_day_extreme_retest_v0.py::build_trade_plan`
