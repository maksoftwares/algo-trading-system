# NY AM Pullback Continuation v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 40-180
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-60%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many failed pullbacks near -1R, fewer 1.5R continuation wins, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a bidirectional XAUUSD New York morning pullback-continuation expert. It tests whether a directional opening drive from 09:30 to 10:00 America/New_York local time that then pulls back and confirms from 10:00 to 12:00 has enough continuation edge to survive Phase 0 costs and concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries and America/New_York local clock handling.
2. Opening drive: use completed M5 bars whose New York local bar-start time is from 09:30 inclusive to 10:00 exclusive. Record first open, high, low, and final close.
3. Trigger window: only completed M5 bars whose New York local bar-start time is from 10:00 inclusive to 12:00 exclusive can trigger.
4. Directional drive gate: long setups require opening-drive close minus opening-drive open to be at least 0.80 times current M5 ATR(14). Short setups require opening-drive close minus opening-drive open to be at most -0.80 times current M5 ATR(14).
5. Long pullback: within the 8 M5 bars before confirmation, price must pull back to the opening-drive midpoint plus no more than 0.15 times current M5 ATR(14), must not trade more than 0.25 times current M5 ATR(14) below the midpoint, and must close at or above the midpoint minus 0.25 times current M5 ATR(14).
6. Long confirmation: the current completed M5 candle must close bullish, close at least 0.20 times current M5 ATR(14) above the opening-drive midpoint, close in the upper 40% of its range, and have body at least 30% of its range.
7. Short pullback: within the 8 M5 bars before confirmation, price must pull back to the opening-drive midpoint minus no more than 0.15 times current M5 ATR(14), must not trade more than 0.25 times current M5 ATR(14) above the midpoint, and must close at or below the midpoint plus 0.25 times current M5 ATR(14).
8. Short confirmation: the current completed M5 candle must close bearish, close at least 0.20 times current M5 ATR(14) below the opening-drive midpoint, close in the lower 40% of its range, and have body at least 30% of its range.
9. Entry: enter at the next eligible M5 open after the confirmation candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
10. Stop: for longs, stop below the pullback low by 0.25 times current M5 ATR(14); for shorts, stop above the pullback high by 0.25 times current M5 ATR(14).
11. Target: use a fixed 1.5R target.
12. Daily duplicate rule: allow at most one setup per New York local date.
13. Invalidation: no setup if opening-drive values, local timestamps, ATR, pullback, or confirmation requirements are unavailable.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/ny_am_pullback_continuation_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is moderate frequency. The candidate should cluster around days where New York creates an early directional impulse and then resumes after a pullback. It should lose when the opening drive is only a liquidity sweep or when the pullback turns into a reversal.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, or a clear rejection if frequency is too low.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

New York morning is one of the densest liquidity windows for gold. A strong early drive followed by a controlled pullback may reflect continuation flow rather than a completed stop run. This candidate tests that sequence with local-time handling and fixed pullback rules.

This candidate is intentionally different from the rejected broad `trend_pullback`. It uses a specific New York opening-drive event and a short intraday continuation window.

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

- Opening-drive feature construction: `src/phase0/strategies/ny_am_pullback_continuation_v0.py::prepare_features`
- Pullback/confirmation trigger: `src/phase0/strategies/ny_am_pullback_continuation_v0.py::_setup_at_position`
- Stop/target construction: `src/phase0/strategies/ny_am_pullback_continuation_v0.py::build_trade_plan`
