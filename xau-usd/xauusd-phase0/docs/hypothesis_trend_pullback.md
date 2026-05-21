# Hypothesis: Trend Pullback Expert

Expert name: Trend Pullback
Hypothesis date: 2026-05-21
Hypothesis version: v1.1-post-review
Author / owner: Phase 0 research desk

## Audit Note

This hypothesis version was completed after an exploratory real-data run exposed that the prior registered file was incomplete. Results generated before this document is registered are exploratory evidence only and must not be used as a clean pre-registered Phase 0 pass.

## Mechanical Definition

Trend Pullback is a completed-bar trend-continuation setup. The H1 chart defines directional bias using EMA(50), EMA(200), EMA(50) slope over 20 bars, and ATR(14). The M15 chart defines pullback context using EMA(21) and ATR(14). The M5 chart supplies entry confirmation using bullish or bearish engulfing and pin-bar patterns.

For a long signal, H1 EMA(50) must be above H1 EMA(200), H1 EMA(50) slope must be positive, the latest completed M15 close must be within 0.5 times H1 ATR(14) of M15 EMA(21), and the M5 bar must print a bullish engulfing or bullish pin-bar confirmation. Entry is simulated at the next available M5 market bar. The stop loss is below the lowest low of the latest 10 completed M5 bars by 0.1 times M15 ATR(14), and the target is 1.5R.

For a short signal, H1 EMA(50) must be below H1 EMA(200), H1 EMA(50) slope must be negative, the latest completed M15 close must be within 0.5 times H1 ATR(14) of M15 EMA(21), and the M5 bar must print a bearish engulfing or bearish pin-bar confirmation. Entry is simulated at the next available M5 market bar. The stop loss is above the highest high of the latest 10 completed M5 bars by 0.1 times M15 ATR(14), and the target is 1.5R.

Only completed bars may be used. The Phase 0 simulator enforces one open position at a time, adverse-first ambiguous intrabar handling, configured spread and commission costs, and no live order placement.

Code mapping:

- H1 trend logic: `src/phase0/strategies/trend_pullback.py::prepare_features`
- Pullback and confirmation logic: `src/phase0/strategies/trend_pullback.py::generate_signals`
- Stop/target construction: `src/phase0/strategies/trend_pullback.py::build_trade_plan`
- Candle definitions: `src/phase0/candles.py`
- Execution simulation: `src/phase0/execution.py`

## Expected Behavior

Expected trade count per year: 800 to 2500 trades on XAUUSD M5, depending on broker coverage and trend persistence.

Expected cost-adjusted PF: 1.15 to 1.45 across accepted matrix cells; at least 7 of 9 cells should meet PF >= 1.30 for approval.

Expected losing-month percentage: 20% to 45%.

Expected worst single month: not worse than -18% starting equity under configured risk.

Expected max consecutive zero months: 0 to 2.

Expected R-multiple distribution: many small stop-loss outcomes near -1R, clustered around pullback failures, balanced by 1.5R trend-continuation winners; average R should be positive in passing cells.

## Why This Hypothesis Should Exist

XAUUSD often trends directionally during macro, liquidity, and session-driven repricing. Pullbacks toward a shorter-term mean inside a higher-timeframe trend may offer continuation entries with defined invalidation. The H1/M15/M5 structure is intended to avoid trading every candle pattern and require trend, pullback, and confirmation alignment.

## What Would Falsify It

The hypothesis is falsified if fewer than 7 of 9 matrix cells achieve PF >= 1.30, if any required cell has too few trades, if drawdown or total-return gates fail, if profit concentration exceeds configured limits, if p95 cost sensitivity falls below the configured ratio, if decile persistence fails, if comparison-symbol checks fail without a documented XAU-specific mechanism, or if manual adversarial review finds logic-gap failures above 25% of reviewed losing trades.
