# Hypothesis: h1_real_yield_dollar_shock_reversal_v0

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Research lane: independent macro shock / intraday reversal
Mechanic family: H1 macro shock reversal
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-96
Expected median hold hours: 2-8
Expected decisions per week: 0-5 during joint macro shock windows
Timeframe diversification qualifies: yes
Expected trade count per year: 60-500
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -22R
Expected max consecutive zero months: 3
Expected R-multiple distribution: sparse H1 reversal losses with clustered 1.40R winners after macro-pressure overshoots; no single trade should dominate net expectancy.
Hypothesis SHA256: pending registration
Expert: `h1_real_yield_dollar_shock_reversal_v0`
Status at registration: research candidate, disabled from live trading

## Mechanical Definition

This candidate tests XAUUSD H1 reversals after a joint real-yield and broad-dollar shock. It uses only completed H1 bars and shifted daily macro observations from FRED DFII10 and DTWEXBGS.

Long setup:

- The 20-business-day real-yield change is at least +0.12.
- The 20-business-day broad-dollar log return is at least +0.0030.
- At least one of the real-yield or broad-dollar 252-day z-scores is at least +0.45.
- XAUUSD has sold off over the prior 12 completed H1 bars by at least -0.20%.
- The prior 6-bar return is not strongly positive.
- The prior 24-bar return is not worse than -2.50%.
- The signal candle is bullish, closes in the upper 42% of its range, and is not more than 2 ATR below H1 EMA50.
- Entry is at market on the completed signal bar close, stop is 0.95 H1 ATR, target is 1.40R, and planned time stop is 8 H1 bars.

Short setup is symmetric:

- Real yield and broad dollar both fall enough to create a gold-supportive macro shock.
- XAUUSD rallies over the prior 12 completed H1 bars by at least +0.20%.
- The signal candle is bearish, closes in the lower 42% of its range, and is not more than 2 ATR above H1 EMA50.
- Entry, stop, target, and time-stop rules mirror the long setup.

The strategy may emit at most one signal per UTC day per direction. It does not use level/retest mechanics, round numbers, discretionary pattern review, future macro values, or live execution logic.

## Expected Behavior

Expected trade count: 40 or more trades per Phase 0 matrix cell.
Expected profit factor: at least 1.30 in 7 of 9 matrix cells.
Expected losing-month percentage: below 45%.
Expected worst month: no single month should dominate the result.
Expected max zero-trade months: 3 or fewer.
Expected R distribution: many small losses, fewer 1.40R winners, and no single trade contributing more than 10% of net profit.

## Why This Hypothesis Should Exist

Real yields and the broad dollar are direct macro pressure variables for gold. A rapid joint rise can force intraday liquidation, while a rapid joint fall can force short-covering and chase behavior. The hypothesis is that some H1 moves after these macro shocks overshoot before reverting when the completed candle shows intraday absorption. This is intended to be an independent macro/reversal behavior family rather than another breakout-retest or level-retest variant.

## What Would Falsify It

The hypothesis is rejected if it fails the Phase 0 research matrix, cannot produce sufficient trade count across brokers, only works on one data vendor, fails cost sensitivity, shows concentration dependence, fails decile persistence, or requires parameter loosening after results are known. It is also rejected if macro coverage is incomplete or if the implementation uses unshifted macro data.
