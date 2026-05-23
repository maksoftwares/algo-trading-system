# Round Number Retest v0 Hypothesis

Hypothesis date: 2026-05-23
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 500-3000
Expected cost-adjusted PF: 1.15-1.50
Expected losing-month percentage: 35%-55%
Expected worst single month: -10R to -30R
Expected max consecutive zero months: 1
Expected R-multiple distribution: Many small failed retests near -1R, fewer +1.5R continuations, and no acceptable pass if one round-number increment or broker/cost cell dominates.

## Mechanical Definition

This candidate is a bidirectional XAUUSD round-number breakout-retest expert. It tests whether fixed psychological handles at 10, 25, and 50 dollar increments act as enough of a public auction reference that a completed M5 break, retest, and continuation trigger survives Phase 0 costs.

This is a same-family candidate relative to `breakout_retest` because it uses break-and-retest mechanics. The independent element is level source: fixed price handles rather than previous daily highs/lows, previous weekly highs/lows, or confirmed swing levels.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 break, retest, and confirmation candles.
2. Round-number levels: candidate levels are fixed price handles at 10, 25, and 50 dollar increments.
3. Long break: a completed M5 candle must close at least 0.30 times current M5 ATR(14) above a round-number level.
4. Long retest: within the next 20 M5 bars, a completed M5 candle must trade back to within 5 points above the level and close at or above the level.
5. Long confirmation: the next completed M5 candle must close bullish.
6. Short break: a completed M5 candle must close at least 0.30 times current M5 ATR(14) below a round-number level.
7. Short retest: within the next 20 M5 bars, a completed M5 candle must trade back to within 5 points below the level and close at or below the level.
8. Short confirmation: the next completed M5 candle must close bearish.
9. Entry: use a stop entry one point beyond the retest candle high for longs and one point beyond the retest candle low for shorts.
10. Stop: for longs, stop below the retest low by 0.10 times M5 ATR(14). For shorts, stop above the retest high by 0.10 times M5 ATR(14).
11. Target: use a fixed 1.5R target.
12. Invalidation: no setup if ATR is unavailable, no nearby round-number break exists, retest/confirmation fails, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is moderate-to-high frequency. Round numbers should create public reference levels where a successful break and hold may attract continuation flow. The candidate should lose when round numbers are noisy, when costs consume the small continuation move, or when the retest sequence is too similar to generic breakout-retest behavior without additional edge.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer should be plausible because round-number behavior is not XAU-only, though XAUUSD may remain the strongest expression.

## Why This Hypothesis Should Exist

Round numbers are widely visible reference prices. If market participants cluster stops, take-profits, and discretionary attention around fixed handles, then a break-and-retest through those handles may create short-term continuation pressure. This candidate tests whether that public level source adds edge beyond arbitrary M5 momentum.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Manual adversarial review finds logic gaps above the allowed threshold.
- The strategy only passes after adding discretionary round-number increments, sessions, volatility, or trend filters after results are known.

Code mapping after implementation:

- ATR-only feature construction: `src/phase0/strategies/round_number_retest_v0.py::RoundNumberRetestV0Strategy.prepare_features`
- Round-number level construction: `src/phase0/strategies/round_number_retest_v0.py::RoundNumberRetestV0Strategy._candidate_levels_from_arrays`
- Break/retest/confirmation mechanics: inherited from `src/phase0/strategies/breakout_retest.py::BreakoutRetestStrategy`
