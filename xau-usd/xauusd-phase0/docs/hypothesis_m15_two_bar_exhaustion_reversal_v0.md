# M15 Two Bar Exhaustion Reversal v0 Hypothesis

Hypothesis date: 2026-05-25
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: completed M15 impulse-exhaustion reversal
Entry / decision timeframe: M15 completed-candle decision, M5 execution sequencing
Expected median hold bars M5-equivalent: 24-96
Expected median hold hours: 2-8
Expected decisions per week: 3-18
Timeframe diversification qualifies: partial; intraday but independent from level/retest mechanics
Expected trade count per year: 80-420
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 45%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many -1R failed fades, smaller number of +1.35R snapback winners, and rejection if one spike window dominates.

## Mechanical Definition

This candidate is a research-only XAUUSD M15 two-bar exhaustion reversal hypothesis. It is not a retest, reclaim, round-number, daily/weekly level, session-extreme, VWAP, sweep, inside-day, outside-day, broad-USD proxy, gold/silver relative-value, learned H1 state, or calendar-drift strategy.

The locked v0 setup is:

1. Market and decision timeframe: XAUUSD completed M15 bars only.
2. Execution timeframe: M5 bars are used by the existing simulator for market-entry and exit sequencing.
3. Feature set: M15 ATR(14), two-bar close-to-close impulse in ATR units, final bar body ratio, prior bar body ratio, final close position, final range in ATR, and the two-bar high/low.
4. Long setup: the last two completed M15 bars are bearish, the two-bar close-to-close impulse is at least 1.55 ATR lower, the final candle closes in the lower 38% of its range, final body ratio is at least 0.38, prior body ratio is at least 0.25, and final range is not above 3.40 ATR.
5. Short setup: symmetric bullish exhaustion rules with a two-bar impulse at least 1.55 ATR higher and final close in the upper 38% of its range.
6. Frequency control: take at most one signal per UTC day and direction.
7. Entry: market entry at the first available M5 execution bar at or after the completed M15 signal timestamp.
8. Stop: beyond the two-bar extreme plus a 0.25 ATR buffer.
9. Target: fixed 1.35R target.
10. Time stop: 96 M5 bars, equivalent to 32 M15 bars, if neither stop nor target is touched.

## Expected Behavior

The candidate is expected to capture short-horizon snapback after unusually directional two-candle acceleration. It should lose when an apparent exhaustion impulse is only the start of a stronger trend. It should not need fixed levels, session windows, cross-symbol data, or post-result regime switches.

Expected evidence profile:

- At least 40 trades in every Phase 0 matrix cell.
- PF above 1.30 in at least 7 of 9 matrix cells if the edge is real.
- Positive decile persistence in at least 8 of 10 deciles if trade count is sufficient.
- Largest-trade and top-five concentration within the existing Phase 0 caps.
- P95-cost PF should retain at least 50% of best-case PF.
- Any pass must remain explainable by the locked M15 impulse-exhaustion features, not by later-added price levels or session filters.

## Why This Hypothesis Should Exist

Many successful and provisional candidates in the current bench are level-and-retest variants. This candidate deliberately ignores external price references and asks whether very short-term XAU acceleration itself has enough mean-reversion structure to become a separate EA family.

The hypothesis should only pass if the raw two-bar exhaustion feature survives across broker windows and cost assumptions. If it is merely a noisy candle-shape fade, the 9-cell matrix should reject it.

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
