# Swing Breakout Retest v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 300-2500
Expected cost-adjusted PF: 1.15-1.50
Expected losing-month percentage: 30%-55%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 1
Expected R-multiple distribution: Many ordinary -1R failed retests, many 1.5R continuation wins, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a breakout-retest continuation expert restricted to latest confirmed M5 swing levels. It tests whether the approved `breakout_retest` behavior survives when previous daily and previous weekly levels are removed and only local swing highs/lows are eligible.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries.
2. Level source: use only latest confirmed M5 swing highs for long setups and latest confirmed M5 swing lows for short setups, using the existing Phase 0 swing confirmation logic with `left=4` and `right=4`.
3. Long breakout: within the 20 M5 bars before the retest candle, a completed M5 candle must close at least 0.30 times ATR(14) above the selected latest confirmed swing high.
4. Long retest: the retest candle must trade back to within 5 points of the swing high and close at or above the swing high.
5. Long confirmation: the confirmation candle must close bullish.
6. Long entry: use a stop entry one point above the retest candle high.
7. Long stop: place the stop 0.10 times retest ATR(14) below the retest candle low.
8. Short breakout: within the 20 M5 bars before the retest candle, a completed M5 candle must close at least 0.30 times ATR(14) below the selected latest confirmed swing low.
9. Short retest: the retest candle must trade back to within 5 points of the swing low and close at or below the swing low.
10. Short confirmation: the confirmation candle must close bearish.
11. Short entry: use a stop entry one point below the retest candle low.
12. Short stop: place the stop 0.10 times retest ATR(14) above the retest candle high.
13. Target: use a fixed 1.5R target.
14. Invalidation: no setup if swing level, ATR, breakout, retest, or confirmation requirements are unavailable.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/swing_breakout_retest_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is higher frequency than daily/weekly level variants. The candidate should capture local continuation after a recent M5 swing is broken and successfully retested. It should lose when local swing breaks are noise rather than continuation.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the swing-only edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

The approved `breakout_retest` expert mixes prior daily, prior weekly, and local swing levels. A swing-only variant tests whether the edge is broad within local market structure rather than dependent on slower calendar levels. This may provide a second deployable candidate, but it remains correlated with the approved expert and must be treated as same-family until proven otherwise.

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

- Base breakout/retest sequence: `src/phase0/strategies/breakout_retest.py`
- Swing-only level filter: `src/phase0/strategies/swing_breakout_retest_v0.py::_candidate_levels_from_arrays`
