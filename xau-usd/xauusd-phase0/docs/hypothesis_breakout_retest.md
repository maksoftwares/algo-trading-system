# Hypothesis: Breakout-Retest Expert

Expert name: Breakout-Retest
Hypothesis date: 2026-05-21
Hypothesis version: v1.1-post-review
Author / owner: Phase 0 research desk

## Audit Note

This hypothesis version was completed after an exploratory real-data run exposed that the prior registered file was incomplete. Results generated before this document is registered are exploratory evidence only and must not be used as a clean pre-registered Phase 0 pass.

## Mechanical Definition

Breakout-Retest is a completed-bar M5 setup that trades retests of visible levels after directional displacement. The level set contains the previous completed daily high or low, previous completed weekly high or low, and the latest confirmed M5 swing high or low.

For a long candidate, a recent M5 close must break above a candidate resistance level by at least 0.3 times M5 ATR(14). The following retest bar must trade back to within 5 points of that level and close at or above the level. A bullish confirmation candle then creates a stop entry one point above the retest high. The stop loss is set below the retest low by 0.1 times retest ATR(14), and the target is 1.5R. The pending entry expires after 5 M5 bars.

For a short candidate, the same logic is mirrored below support: a recent M5 close must break below the candidate level by at least 0.3 times M5 ATR(14), the retest bar must trade back to within 5 points and close at or below the level, then a bearish confirmation candle creates a stop entry one point below the retest low. The stop loss is above the retest high by 0.1 times retest ATR(14), and the target is 1.5R. The pending entry expires after 5 M5 bars.

Only completed bars may be used. The Phase 0 simulator enforces one open position at a time, adverse-first ambiguous intrabar handling, configured spread and commission costs, and no live order placement.

Code mapping:

- Level construction: `src/phase0/levels.py`
- Signal generation: `src/phase0/strategies/breakout_retest.py::BreakoutRetestStrategy.generate_signals`
- Candidate selection: `src/phase0/strategies/breakout_retest.py::_long_candidates` and `_short_candidates`
- Stop/target construction: `src/phase0/strategies/breakout_retest.py::build_trade_plan`
- Execution simulation: `src/phase0/execution.py`

## Expected Behavior

Expected trade count per year: 1800 to 3200 trades on XAUUSD M5, depending on broker coverage and cost model.

Expected cost-adjusted PF: 1.20 to 1.60 across accepted matrix cells; at least 7 of 9 cells should meet PF >= 1.30.

Expected losing-month percentage: 10% to 35%.

Expected worst single month: not worse than -15% starting equity under configured risk.

Expected max consecutive zero months: 0 to 1.

Expected R-multiple distribution: median losing trade near -1R, frequent small losses, and a right tail from 1.5R target hits; average R should remain positive after costs.

## Why This Hypothesis Should Exist

XAUUSD frequently revisits visible session, daily, weekly, and swing levels after displacement. A retest-and-confirmation structure attempts to avoid first-touch breakouts while still entering before the continuation leg is fully mature. The setup should benefit from high participation around visible levels and should remain testable across Capital.com, Pepperstone, and Dukascopy bar histories.

## What Would Falsify It

The hypothesis is falsified if fewer than 7 of 9 matrix cells achieve PF >= 1.30, if any required cell has too few trades, if drawdown or total-return gates fail, if profit concentration exceeds the configured limits, if p95 cost sensitivity falls below the configured ratio, if decile persistence fails, if EURUSD or USDJPY multisymbol PF falls below 0.90 without a documented XAU-specific mechanism, or if manual adversarial review finds logic-gap failures above 25% of reviewed losing trades.
