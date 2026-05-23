# Symbol-Normalized Round Retest v0 Hypothesis

Hypothesis date: 2026-05-23
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 300-2500
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-58%
Expected worst single month: -10R to -35R
Expected max consecutive zero months: 1
Expected R-multiple distribution: Many small failed retests near -1R, fewer +1.5R continuations, and no acceptable pass if one symbol-scale level increment or one broker/cost cell dominates.

## Mechanical Definition

This candidate is a bidirectional round-number breakout-retest expert that scales its fixed handles by symbol. It is a fresh versioned hypothesis, not a tuning edit to `round_number_retest_v0`.

The candidate tests whether public price handles produce continuation after completed-candle break, retest, and confirmation across symbols with different quote precision. It is same-family relative to `breakout_retest` and `round_number_retest_v0`; the new independent element is symbol-normalized level construction.

The mechanical setup is:

1. Market and timeframe: XAUUSD, EURUSD, and USDJPY with M5 break, retest, and confirmation candles.
2. XAUUSD round-number levels: 10.0, 25.0, and 50.0 dollar increments.
3. EURUSD round-number levels: 0.0050, 0.0100, and 0.0250 increments.
4. USDJPY round-number levels: 0.50, 1.00, and 2.50 increments.
5. Long break: a completed M5 candle must close at least 0.30 times current M5 ATR(14) above a symbol-scaled round-number level.
6. Long retest: within the next 20 M5 bars, a completed M5 candle must trade back to within 5 points above the level and close at or above the level.
7. Long confirmation: the next completed M5 candle must close bullish.
8. Short break: a completed M5 candle must close at least 0.30 times current M5 ATR(14) below a symbol-scaled round-number level.
9. Short retest: within the next 20 M5 bars, a completed M5 candle must trade back to within 5 points below the level and close at or below the level.
10. Short confirmation: the next completed M5 candle must close bearish.
11. Entry: use a stop entry one point beyond the retest candle high for longs and one point beyond the retest candle low for shorts.
12. Stop: for longs, stop below the retest low by 0.10 times M5 ATR(14). For shorts, stop above the retest high by 0.10 times M5 ATR(14).
13. Target: use a fixed 1.5R target.
14. Invalidation: no setup if ATR is unavailable, no nearby symbol-scaled round-number break exists, retest/confirmation fails, or stop/target construction creates non-positive risk.

## Expected Behavior

Expected behavior is moderate-to-high frequency. Symbol-scaled round numbers should create public reference levels where a successful break and hold may attract continuation flow. XAUUSD may remain the strongest expression, but this version should avoid zero-trade multisymbol starvation caused by XAU-sized handles on FX pairs.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY should produce non-zero transfer evidence; if transfer still fails, any pass must be labeled XAU-specific and not diversification.

## Why This Hypothesis Should Exist

Round-number attention is not unique to gold, but the absolute price increment that attracts attention differs by symbol. A 10-dollar XAU handle is not comparable to a 10.00000 EURUSD move. Normalizing handle increments by symbol should test the same public-reference mechanism without starving FX comparison symbols.

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
- Multisymbol evidence remains zero-trade or weak while the candidate is represented as diversification.

Code mapping after implementation:

- ATR-only feature construction: `src/phase0/strategies/round_number_retest_v0.py::RoundNumberRetestV0Strategy.prepare_features`
- Symbol-scaled level construction: `src/phase0/strategies/symbol_normalized_round_retest_v0.py::SymbolNormalizedRoundRetestV0Strategy._candidate_levels_from_arrays`
- Break/retest/confirmation mechanics: inherited from `src/phase0/strategies/breakout_retest.py::BreakoutRetestStrategy`
