# Symbol Round Sweep Reversal v0 Hypothesis

Hypothesis date: 2026-05-23
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 300-2500
Expected cost-adjusted PF: 1.05-1.40
Expected losing-month percentage: 38%-60%
Expected worst single month: -10R to -35R
Expected max consecutive zero months: 1
Expected R-multiple distribution: Many failed fades near -1R, fewer +1.5R reversal wins, and no acceptable pass if the result depends on one symbol, one handle increment, or one broker/cost cell.

## Mechanical Definition

This candidate is a bidirectional symbol-scaled round-number sweep reversal expert. It tests the opposite behavior from the breakout-retest family: price pushes through a public handle, fails to hold beyond it, and closes back through the handle with rejection structure.

The mechanical setup is:

1. Market and timeframe: XAUUSD, EURUSD, and USDJPY with M5 signal candles.
2. XAUUSD round-number levels: 10.0, 25.0, and 50.0 dollar increments.
3. EURUSD round-number levels: 0.0050, 0.0100, and 0.0250 increments.
4. USDJPY round-number levels: 0.50, 1.00, and 2.50 increments.
5. Long sweep: an M5 candle must trade at least 0.20 times M5 ATR(14) below a symbol-scaled round-number level.
6. Long reclaim: the same completed M5 candle must close at least 0.05 times M5 ATR(14) back above the level.
7. Long rejection structure: candle closes bullish, close is in the upper 40% of the range, body is at least 20% of range, and the lower wick is at least 1.25 times the body.
8. Short sweep: an M5 candle must trade at least 0.20 times M5 ATR(14) above a symbol-scaled round-number level.
9. Short reclaim: the same completed M5 candle must close at least 0.05 times M5 ATR(14) back below the level.
10. Short rejection structure: candle closes bearish, close is in the lower 40% of the range, body is at least 20% of range, and the upper wick is at least 1.25 times the body.
11. Entry: market at the signal close in the Phase 0 simulator.
12. Stop: beyond the signal candle extreme by 0.10 times M5 ATR(14).
13. Target: fixed 1.5R target.
14. Invalidation: no setup if ATR is unavailable, the candle does not sweep and reclaim a symbol-scaled handle, the rejection structure fails, or stop/target construction creates non-positive risk.

## Expected Behavior

Expected behavior is moderate-to-high frequency with lower win rate but positive skew if public handle sweeps trap late continuation traders. It should be more independent than breakout-retest because it fades failed breaks rather than joining successful breaks.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is strong enough for the current gate set.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY should produce non-zero transfer evidence because the level definition is symbol-scaled.

## Why This Hypothesis Should Exist

Round numbers can attract stops and breakout attempts. If a candle sweeps beyond a widely visible handle and closes back through it with a large rejection wick, short-horizon participants may be trapped on the wrong side of the level. That trapped flow can support a short reversal move.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Manual adversarial review finds logic gaps above the allowed threshold.
- The strategy only passes after adding post-result discretionary sessions, trend filters, or handle increments.

Code mapping after implementation:

- ATR feature construction: `src/phase0/strategies/symbol_round_sweep_reversal_v0.py::SymbolRoundSweepReversalV0Strategy.prepare_features`
- Symbol-scaled sweep level construction: `src/phase0/strategies/symbol_round_sweep_reversal_v0.py::SymbolRoundSweepReversalV0Strategy._candidate_low_sweep_levels`
- Reversal trigger construction: `src/phase0/strategies/symbol_round_sweep_reversal_v0.py::SymbolRoundSweepReversalV0Strategy._setup_at_position`
- Stop/target construction: `src/phase0/strategies/symbol_round_sweep_reversal_v0.py::SymbolRoundSweepReversalV0Strategy.build_trade_plan`
