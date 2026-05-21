# Hypothesis: Range Mean-Reversion Expert

Expert name: Range Mean-Reversion
Hypothesis date: 2026-05-21
Hypothesis version: v1.1-post-review
Author / owner: Phase 0 research desk

## Audit Note

This hypothesis version was completed after an exploratory real-data run exposed that the prior registered file was incomplete. Results generated before this document is registered are exploratory evidence only and must not be used as a clean pre-registered Phase 0 pass.

## Mechanical Definition

Range Mean-Reversion is a completed-bar reversal setup. H1 ADX(14) defines whether the market is in a low-trend regime. M15 bars define a 50-bar range using the highest high and lowest low. M15 ATR(14) defines minimum range width and stop distance. M5 pin bars provide boundary rejection confirmation.

A valid range state requires the latest 20 completed H1 ADX(14) values to remain below 20. The latest 50 completed M15 bars must form a range at least 2.0 times M15 ATR(14) wide, with at least three touches near the upper boundary and at least three touches near the lower boundary. A long signal occurs when an M5 bullish pin bar trades into the lower boundary zone. A short signal occurs when an M5 bearish pin bar trades into the upper boundary zone.

For a long trade, the limit entry is the lower boundary, the stop loss is 0.3 times M15 ATR(14) below the lower boundary, and the target is the upper boundary. For a short trade, the limit entry is the upper boundary, the stop loss is 0.3 times M15 ATR(14) above the upper boundary, and the target is the lower boundary. Reward/risk must be at least 1.0, and the pending order expires after 6 M5 bars.

Only completed bars may be used. The Phase 0 simulator enforces one open position at a time, adverse-first ambiguous intrabar handling, configured spread and commission costs, and no live order placement.

Code mapping:

- H1 regime and M15 range features: `src/phase0/strategies/range_mr.py::prepare_features`
- Range state and boundary confirmation: `src/phase0/strategies/range_mr.py::generate_signals`
- Stop/target construction: `src/phase0/strategies/range_mr.py::build_trade_plan`
- Pin-bar definitions: `src/phase0/candles.py`
- Execution simulation: `src/phase0/execution.py`

## Expected Behavior

Expected trade count per year: 20 to 200 trades on XAUUSD M5, because strict low-ADX and range-touch filters should reduce activity.

Expected cost-adjusted PF: 1.05 to 1.40 across accepted matrix cells; at least 7 of 9 cells should meet PF >= 1.30 for approval.

Expected losing-month percentage: 25% to 55%.

Expected worst single month: not worse than -12% starting equity under configured risk.

Expected max consecutive zero months: 0 to 3.

Expected R-multiple distribution: fewer trades than the other candidates, with stop-loss losses near -1R and occasional wider mean-reversion wins when the opposite boundary is reached.

## Why This Hypothesis Should Exist

XAUUSD alternates between directional expansion and congestion. During low-trend periods, repeated boundary touches can indicate two-way auction behavior where rejection candles near range extremes may offer asymmetric reversion entries. The hypothesis should only survive if range activity is frequent enough and robust across broker windows.

## What Would Falsify It

The hypothesis is falsified if fewer than 7 of 9 matrix cells achieve PF >= 1.30, if any required cell has too few trades, if drawdown or total-return gates fail, if profit concentration exceeds configured limits, if p95 cost sensitivity falls below the configured ratio, if decile persistence fails, if comparison-symbol checks fail without a documented XAU-specific mechanism, or if manual adversarial review finds logic-gap failures above 25% of reviewed losing trades.
