# H1 Macro Composite Pullback v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: Macro-composite state with H1 pullback continuation
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 36-144
Expected median hold hours: 3-12
Expected decisions per week: 0-12
Timeframe diversification qualifies: yes
Expected trade count per year: 80-500
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 40%-80%
Expected worst single month: -10R to -22R
Expected max consecutive zero months: 2
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.50R continuations when the fixed macro vote and H1 pullback timing align. Reject if results require changing macro vote thresholds, H1 EMA rules, decision hours, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

Important audit note: this is result-informed by the `h4_macro_composite_risk_state_v0` near miss, which reached 6/9 PF cells but failed sample, activity, and concentration. This candidate is a new locked hypothesis that tests whether H1 pullback timing can increase sample size without relying on XAU level retests.

## Mechanical Definition

`h1_macro_composite_pullback_v0` tests whether a fixed public macro/risk vote can define a gold directional state, with entries only when XAU makes an H1 pullback/continuation candle in that direction.

Data source:

- FRED real-yield and broad-dollar proxy data.
- FRED breakeven inflation data.
- FRED Treasury-rate and curve data.
- FRED credit-spread data.
- FRED VIX and GVZ volatility data.
- FRED financial-conditions data.
- All macro features are shifted before being merged into XAUUSD H1 bars.

Signal rules:

1. Use only XAUUSD H1 decision bars ending at 08:00, 12:00, 16:00, or 20:00 UTC.
2. Compute the same fixed macro vote family used by `h4_macro_composite_risk_state_v0`.
3. Long setup:
   - macro composite score >= 3
   - macro bull votes >= 4
   - H1 close is above EMA50
   - H1 EMA21 is above or equal to EMA50
   - the H1 bar touches or pulls back near EMA21
   - 24-bar H1 return is non-negative
   - 6-bar H1 return is not strongly negative
   - H1 candle closes bullish with close location >= 0.54
4. Short setup:
   - macro composite score <= -3
   - macro bear votes >= 4
   - H1 close is below EMA50
   - H1 EMA21 is below or equal to EMA50
   - the H1 bar touches or pulls back near EMA21
   - 24-bar H1 return is non-positive
   - 6-bar H1 return is not strongly positive
   - H1 candle closes bearish with close location <= 0.46
5. Entry is simulated at market from the H1 signal close.
6. Stop is 1.15 x H1 ATR14 from entry.
7. Target is 1.50R.
8. Time stop is 12 H1 bars.
9. Maximum one signal per UTC day per direction.

## Expected Behavior

Expected trade count: moderate H1 frequency, likely 80-500 trades per year if the macro state persists long enough for H1 pullbacks.
Expected PF: at least 1.30 in 7 of 9 matrix cells if macro state plus H1 timing improves the H4 macro-composite near miss.
Expected losing-month percentage: below 50%.
Expected worst month: no worse than -10R on fixed-notional reporting.
Expected zero-trade months: no more than 2 consecutive months.

## Why This Hypothesis Should Exist

The H4 macro-composite v0 was one of the strongest independent non-level near misses: 6/9 PF cells, positive returns in all cells, but not enough Capital.com trades and too much concentration/activity risk. A faster H1 timing layer may convert persistent macro states into more observations while keeping the economic mechanism independent from breakout-retest and round-number retest logic.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 2
- the data source cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
