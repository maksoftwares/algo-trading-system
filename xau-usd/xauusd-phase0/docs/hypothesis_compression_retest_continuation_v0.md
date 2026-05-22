# Compression Retest Continuation v0 Hypothesis

Hypothesis date: 2026-05-22
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 30-150
Expected cost-adjusted PF: 1.10-1.45
Expected losing-month percentage: 35%-60%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many failed retests near -1R, fewer 1.5R continuation wins, and no dependence on one outsized winner.

## Mechanical Definition

This candidate is a bidirectional XAUUSD compression-retest continuation expert. It tests whether a break from a compressed M15 range that retests and holds the broken boundary has enough continuation edge to survive Phase 0 costs and concentration gates.

The mechanical setup is:

1. Market and timeframe: XAUUSD with M5 entries and M15 compression context.
2. Compression range: use the latest completed M15 16-bar high-low range.
3. Compression gate: the latest completed M15 16-bar range width must be below the 35th percentile of the prior 120 completed M15 16-bar widths.
4. Long breakout: within the 12 M5 bars before confirmation, a completed M5 candle must close at least 0.20 times current M5 ATR(14) above the M15 compression high and close bullish.
5. Long retest: after the long breakout and before confirmation, a completed M5 candle must trade back to within 0.15 times current M5 ATR(14) above the compression high and close no more than 0.10 times current M5 ATR(14) below the compression high.
6. Long confirmation: the current completed M5 candle must close bullish, close at least 0.10 times current M5 ATR(14) above the compression high, close in the upper 40% of its range, and have body at least 30% of its range.
7. Short breakout: within the 12 M5 bars before confirmation, a completed M5 candle must close at least 0.20 times current M5 ATR(14) below the M15 compression low and close bearish.
8. Short retest: after the short breakout and before confirmation, a completed M5 candle must trade back to within 0.15 times current M5 ATR(14) below the compression low and close no more than 0.10 times current M5 ATR(14) above the compression low.
9. Short confirmation: the current completed M5 candle must close bearish, close at least 0.10 times current M5 ATR(14) below the compression low, close in the lower 40% of its range, and have body at least 30% of its range.
10. Entry: enter at the next eligible M5 open after the confirmation candle, using the existing Phase 0 cost model and one-position-at-a-time rule.
11. Stop: for longs, stop below the lesser of the compression low or retest low by 0.25 times current M5 ATR(14); for shorts, stop above the greater of the compression high or retest high by 0.25 times current M5 ATR(14).
12. Target: use a fixed 1.5R target.
13. Cooldown: ignore additional signals for 24 M5 bars after a generated signal.
14. Invalidation: no setup if compression, ATR, breakout, retest, or confirmation requirements are unavailable.

Implementation status:

The matching disabled research strategy is `src/phase0/strategies/compression_retest_continuation_v0.py`. It is not part of the active Phase 0 `all` registry and is not an approved EA.

## Expected Behavior

Expected behavior is moderate-to-low frequency. The candidate should cluster around contained ranges that break, retest, and then resume. It should lose when compression breaks are false or when the retest hold is only a temporary pause.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell, or a clear rejection if frequency is too low.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- EURUSD and USDJPY transfer may be weaker than XAUUSD, but should not collapse below the multisymbol PF threshold without a written XAU-specific defense.

## Why This Hypothesis Should Exist

Compression can precede directional expansion, but immediate breakout entries are often vulnerable to first-pullback failure. This candidate requires the breakout to survive a retest before entering, making it mechanically distinct from the rejected `squeeze_breakout_long_v0` immediate breakout idea.

This candidate is intentionally related to, but narrower than, `breakout_retest`: it only tests breaks from a statistically compressed M15 range and requires the retest sequence to occur within a fixed M5 window.

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

- Compression feature construction: `src/phase0/strategies/compression_retest_continuation_v0.py::prepare_features`
- Break/retest/confirmation trigger: `src/phase0/strategies/compression_retest_continuation_v0.py::_setup_at_position`
- Stop/target construction: `src/phase0/strategies/compression_retest_continuation_v0.py::build_trade_plan`
