# Asia Range London Breakout v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 60-240
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-60%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many false breakouts near -1R, fewer 1.5R London expansion wins, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a bidirectional XAUUSD Asia-range London breakout expert. It tests whether the first completed-candle London expansion out of a completed Asia range has enough continuation edge to survive Phase 0 costs and concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries, M15 range-normalization context, and UTC session windows.
2. Asia range: use completed M5 bars whose bar-start time is from 00:00 UTC inclusive to 06:00 UTC exclusive. The highest high is the Asia high and the lowest low is the Asia low for that UTC date.
3. London trigger window: only completed M5 bars whose bar-start time is from 07:00 UTC inclusive to 10:00 UTC exclusive can trigger.
4. Range sanity gate: the completed Asia range width must be at least 1.0 times and at most 10.0 times the latest completed M15 ATR(14).
5. Long breakout: the London M5 bar must close at least 0.25 times current M5 ATR(14) above the Asia high, close bullish, close in the upper 40% of its high-low range, and have body at least 35% of its high-low range.
6. Short breakout: the London M5 bar must close at least 0.25 times current M5 ATR(14) below the Asia low, close bearish, close in the lower 40% of its high-low range, and have body at least 35% of its high-low range.
7. Entry: enter at the next eligible M5 open after the breakout candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
8. Stop: for longs, stop below the breakout candle low by 0.25 times current M5 ATR(14); for shorts, stop above the breakout candle high by 0.25 times current M5 ATR(14).
9. Target: use a fixed 1.5R target.
10. Daily duplicate rule: allow at most one London breakout setup per UTC date.
11. Invalidation: no setup if Asia range values, ATR values, session timestamps, or breakout candle requirements are unavailable.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/asia_range_london_breakout_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is moderate frequency. The candidate should cluster around London liquidity expansion after a contained Asia session and should lose when the first expansion is only a stop run.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, or a clear rejection if frequency is too low.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

Gold often forms a contained overnight range before London liquidity expands participation. Some London breaks are false, but the first completed-candle break may represent genuine flow when it closes decisively outside the Asia range. This candidate tests that behavior with fixed session windows and no discretionary news labels.

This candidate is intentionally different from `ny_failed_london_reversal_v0`. It tests continuation from Asia into London, not reversal after London has already established a range.

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

- Asia range and session feature construction: `src/phase0/strategies/asia_range_london_breakout_v0.py::prepare_features`
- London breakout trigger: `src/phase0/strategies/asia_range_london_breakout_v0.py::_setup_at_position`
- Stop/target construction: `src/phase0/strategies/asia_range_london_breakout_v0.py::build_trade_plan`
