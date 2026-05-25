# H1 Smooth Trend Exhaustion Reversal v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 smooth-trend exhaustion reversal
Entry / decision timeframe: H1 completed-candle decision, with M5 used only as execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 144-576
Expected median hold hours: 12-48
Expected decisions per week: 2-8
Timeframe diversification qualifies: yes
Expected trade count per year: 80-260
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Frequent small failed reversals near -1R, fewer +1.4R mean-reversion winners, and rejection if one crisis stretch dominates the total result.

## Mechanical Definition

This candidate is a bidirectional H1 exhaustion reversal expert. It is not a retest, reclaim, round-number, daily/weekly level, session-extreme, VWAP, sweep, inside-day, outside-day, or cross-symbol strategy. It tests whether a smooth one-way 24-hour XAUUSD move becomes temporarily overextended versus H1 EMA and ATR, then mean-reverts after a completed H1 reversal candle.

The mechanical setup is:

1. Market and decision timeframe: XAUUSD H1. M5 bars are used only by the existing simulator for market-entry and exit sequencing.
2. Indicators: H1 ATR(14), H1 EMA(50), 24-hour net move in ATR units, and 24-hour trend efficiency defined as absolute 24-hour net move divided by the sum of absolute one-hour close-to-close moves over the same window.
3. Smooth exhaustion filter: 24-hour trend efficiency must be at least 0.58, so noisy back-and-forth movement is excluded.
4. Long setup state: 24-hour net move must be less than or equal to -2.20 ATR and the H1 close must be at least 1.00 ATR below EMA(50).
5. Short setup state: 24-hour net move must be greater than or equal to +2.20 ATR and the H1 close must be at least 1.00 ATR above EMA(50).
6. Long reversal trigger: the completed H1 candle closes above its open, its body is at least 25% of candle range, it closes in the upper 38% of its range, and candle range is between 0.35 and 2.60 ATR.
7. Short reversal trigger: the completed H1 candle closes below its open, its body is at least 25% of candle range, it closes in the lower 38% of its range, and candle range is between 0.35 and 2.60 ATR.
8. Frequency control: take at most one signal per UTC day and direction.
9. Entry: market entry at the first available M5 execution bar at or after the completed H1 signal timestamp.
10. Stop: for long setups, stop below the H1 signal candle low by 0.35 ATR. For short setups, stop above the H1 signal candle high by 0.35 ATR.
11. Target: fixed 1.40R.
12. Time stop: exit after 48 H1 hours if neither stop nor target has filled.
13. Invalidation: no setup if H1 indicators are unavailable, ATR is non-positive, the smooth-trend filter fails, the reversal candle quality fails, or stop/target construction creates non-positive risk.

Implementation status:

The research-only strategy implementation is mapped below. The candidate is disabled from the active Phase 0 registry and can only be run through explicit research commands.

## Expected Behavior

Expected behavior is short-horizon mean reversion after a smooth, stretched H1 trend leg. The hypothesis should not need a prior high/low, liquidity sweep, session boundary, or round price. It should lose when stretched H1 trends continue without pausing.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- The candidate should provide genuine diversification only if median hold time is meaningfully longer than M5 retest systems and signals are not concentrated in one broker window.

## Why This Hypothesis Should Exist

Gold often makes smooth one-way H1 repricing legs during macro or liquidity-pressure periods. Some of those legs continue, but others become overextended after directional flow is temporarily exhausted. This hypothesis tests the specific case where the prior 24 hours were efficient rather than noisy, the close is stretched versus EMA(50), and the latest H1 candle shows mechanical reversal pressure.

The idea is independent because it does not ask price to reclaim a level, retest a breakout, sweep a prior extreme, or align with a session box. It uses only the shape and efficiency of recent H1 movement.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one isolated crisis stretch or one broker/date window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds retest, fixed-level, round-number, session-extreme, or discretionary news filters after results are known.

Code mapping after implementation:

- H1 feature construction: `src/phase0/strategies/h1_smooth_trend_exhaustion_reversal_v0.py::H1SmoothTrendExhaustionReversalV0Strategy.prepare_features`
- H1 setup trigger: `src/phase0/strategies/h1_smooth_trend_exhaustion_reversal_v0.py::H1SmoothTrendExhaustionReversalV0Strategy._setup_at_row`
- Stop/target/time-stop construction: `src/phase0/strategies/h1_smooth_trend_exhaustion_reversal_v0.py::H1SmoothTrendExhaustionReversalV0Strategy.build_trade_plan`
