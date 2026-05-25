# M15 Two Bar Impulse Continuation v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: completed M15 impulse-continuation
Entry / decision timeframe: M15 completed-candle decision, M5 execution sequencing
Expected median hold bars M5-equivalent: 12-48
Expected median hold hours: 1-4
Expected decisions per week: 3-18
Timeframe diversification qualifies: partial; intraday but independent from level/retest mechanics
Expected trade count per year: 80-420
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 40%-65%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many small failed continuation attempts, more frequent +1.20R follow-through wins if impulse persistence is real, and rejection if one spike window dominates.

## Mechanical Definition

This candidate is a research-only XAUUSD M15 two-bar impulse continuation hypothesis. It is not a retest, reclaim, round-number, daily/weekly level, session-extreme, VWAP, sweep, inside-day, outside-day, broad-USD proxy, gold/silver relative-value, learned H1 state, or calendar-drift strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD completed M15 bars only.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. Feature set: M15 ATR(14), two-bar close-to-close impulse in ATR units, final bar body ratio, prior bar body ratio, final close position, final range in ATR, and the two-bar high/low.
4. Long setup: the last two completed M15 bars are bullish, the two-bar close-to-close impulse is at least 1.55 ATR higher, the final candle closes in the upper 38% of its range, final body ratio is at least 0.38, prior body ratio is at least 0.25, and final range is not above 3.40 ATR.
5. Short setup: symmetric bearish impulse rules with a two-bar impulse at least 1.55 ATR lower and final close in the lower 38% of its range.
6. Frequency control: take at most one signal per UTC day and direction.
7. Entry: market entry at the first available M5 execution bar at or after the completed M15 signal timestamp.
8. Stop: beyond the opposite two-bar extreme plus a 0.25 ATR buffer.
9. Target: fixed 1.20R target.
10. Time stop: 48 M5 bars, equivalent to 16 M15 bars, if neither stop nor target is touched.

## Expected Behavior

The candidate is expected to capture short-horizon continuation after unusually directional two-candle acceleration. It should lose when a sharp impulse exhausts immediately and mean-reverts. It should not need fixed levels, session windows, cross-symbol data, or post-result regime switches.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked M15 impulse-continuation features, not by later-added price levels or session filters.

## Why This Hypothesis Should Exist

The earlier M15 exhaustion-reversal candidate directly tested whether sharp two-bar acceleration should be faded. This separate candidate asks the opposite behavioral question: whether the same kind of completed-candle acceleration has short-horizon persistence. It remains a separate v0 because the entry direction, stop geometry, target multiple, and falsification claim are locked before its first matrix run.

The hypothesis should only pass if raw M15 impulse persistence survives across broker windows and cost assumptions. If the behavior is only noise or a transient trend burst, the 9-cell matrix should reject it.

## What Would Falsify It

The hypothesis is falsified if any of the following occur in a clean Phase 0 run:

- Fewer than 7 of 9 matrix cells reach PF 1.30.
- Any matrix cell has fewer than 40 trades.
- Max drawdown exceeds the Phase 0 threshold.
- Largest-trade or top-five concentration exceeds the Phase 0 caps.
- Decile persistence fails the existing decile gate.
- P95-cost PF divided by best-case PF falls below 0.50.
- Most profits come from one isolated broker/date window.
- Manual adversarial review finds logic gaps above the allowed threshold.
- Any future improvement adds retest, fixed-level, round-number, session-extreme, cross-symbol, or discretionary news filters after results are known.
