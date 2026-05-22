# NY Failed London Reversal v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 40-180
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-60%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many failed reversal attempts near -1R, fewer 1.5R reversal completions, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a bidirectional XAUUSD New York reversal expert. It tests whether a New York sweep through the completed London range that immediately fails back inside the range has enough reversal edge to survive Phase 0 costs and concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries, M15 range-normalization context, and UTC session windows.
2. London range: use completed M5 bars whose bar-start time is from 07:00 UTC inclusive to 11:00 UTC exclusive. The highest high is the London high and the lowest low is the London low for that UTC date.
3. New York evaluation window: only completed M5 bars whose bar-start time is from 13:30 UTC inclusive to 16:30 UTC exclusive can trigger.
4. Range sanity gate: the completed London range width must be at least 1.0 times and at most 10.0 times the latest completed M15 ATR(14).
5. Failed-high short: the New York M5 bar must trade at least 0.35 times current M5 ATR(14) above the London high, then close at least 0.10 times current M5 ATR(14) back below the London high.
6. Failed-high rejection candle: the failed-high bar must close bearish, close in the lower 45% of its high-low range, and have body at least 35% of its high-low range.
7. Failed-low long: the New York M5 bar must trade at least 0.35 times current M5 ATR(14) below the London low, then close at least 0.10 times current M5 ATR(14) back above the London low.
8. Failed-low rejection candle: the failed-low bar must close bullish, close in the upper 45% of its high-low range, and have body at least 35% of its high-low range.
9. Entry: enter at the next eligible M5 open after the failed sweep candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
10. Stop: for shorts, stop above the sweep high by 0.25 times current M5 ATR(14); for longs, stop below the sweep low by 0.25 times current M5 ATR(14).
11. Target: use a fixed 1.5R target.
12. Daily duplicate rule: allow at most one failed-high short and one failed-low long per UTC date.
13. Invalidation: no setup if London range values, ATR values, session timestamps, or rejection candle requirements are unavailable.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/ny_failed_london_reversal_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is moderate frequency. The candidate should cluster around New York liquidity discovery after London has already established a visible range. It should lose when a sweep becomes a genuine session breakout instead of a failed auction.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, or a clear rejection if frequency is too low.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

Gold often reprices around London and New York liquidity handoff. A New York sweep through the London range can represent either true continuation or a stop run that fails once liquidity is taken. This candidate tests the failed-auction version of that behavior with fixed session windows and completed-candle rejection rules.

This candidate is intentionally different from `breakout_retest`. It tests rejection back inside a completed session range, not continuation after a level break and retest.

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

- London range and session feature construction: `src/phase0/strategies/ny_failed_london_reversal_v0.py::prepare_features`
- New York failed-sweep trigger: `src/phase0/strategies/ny_failed_london_reversal_v0.py::_setup_at_position`
- Stop/target construction: `src/phase0/strategies/ny_failed_london_reversal_v0.py::build_trade_plan`
