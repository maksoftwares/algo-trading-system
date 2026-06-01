# H4 Daily Range Extension Reversal v0 Hypothesis

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 daily range-exhaustion reversal
Entry / decision timeframe: H4 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 96-288
Expected median hold hours: 8-24
Expected decisions per week: 1-8
Timeframe diversification qualifies: yes
Expected trade count per year: 60-260
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.25R reversals after an H4 candle rejects an extended UTC-day range. Reject if results require changing the extension threshold, decision hours, close-back rule, stop buffer, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

This candidate is deliberately OHLC-only and higher-timeframe. It is not a breakout-retest, round-level, GLD-flow, macro-proxy, or same-family level-pullback hypothesis.

## Mechanical Definition

`h4_daily_range_extension_reversal_v0` tests whether XAUUSD has a cost-resistant H4 mean-reversion behavior after the current UTC day has already consumed a large fraction of its normal daily range and the current H4 candle rejects the extension.

Data source:

- XAUUSD H4 OHLC bars.
- XAUUSD D1 OHLC bars for the prior 20-day median daily range.
- M5 bars are used only by the Phase 0 execution simulator after the H4 signal is generated.
- No external macro, ETF, futures-volume, news, or options-skew data is required.

Signal rules:

1. Use only completed H4 decision bars ending at 08:00, 12:00, 16:00, or 20:00 UTC.
2. Compute H4 ATR14 from H4 OHLC.
3. Compute the UTC-day open, high-so-far, and low-so-far using only H4 bars completed so far in the current UTC day.
4. Compute the prior D1 20-day median range from completed D1 bars only.
5. A valid H4 candle must have:
   - H4 range >= 0.60 x H4 ATR14
   - H4 body ratio >= 0.22
6. Short setup:
   - day high-so-far minus day open >= 0.85 x prior D1 20-day median range
   - current H4 high touches the day high-so-far within 0.10 x H4 ATR14
   - current H4 close is below current H4 open
   - current H4 close location is <= 0.35 of its own range
7. Long setup:
   - day open minus day low-so-far >= 0.85 x prior D1 20-day median range
   - current H4 low touches the day low-so-far within 0.10 x H4 ATR14
   - current H4 close is above current H4 open
   - current H4 close location is >= 0.65 of its own range
8. Entry is simulated at market from the next available M5 bar after the H4 signal.
9. Long stop: day low-so-far minus 0.25 x H4 ATR14.
10. Short stop: day high-so-far plus 0.25 x H4 ATR14.
11. Target is 1.25R.
12. Time stop is 6 H4 bars.
13. Maximum one signal per UTC day.

## Expected Behavior

Expected trade count: moderate H4 frequency, likely 60-260 trades per year if extended H4 rejection is common enough across brokers.
Expected PF: at least 1.30 in 7 of 9 matrix cells if H4 daily range exhaustion has persistent XAU mean-reversion value after costs.
Expected losing-month percentage: below 60%.
Expected worst month: no worse than -12R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

The current approved family is a high-frequency M5 breakout-retest family that is very sensitive to transaction cost. This candidate asks a different question: after XAU has already spent most of its normal daily range, does a completed H4 rejection candle provide a lower-frequency reversal edge that can survive wider stops and fewer entries?

The mechanism is range exhaustion, not level retest. If it works, it could reduce cost pressure because entries are H4-cadenced and trades use wider H4 stops.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the edge appears only in one broker window
- the only profitable cells depend on best-case costs

Do not tune v0 thresholds after first-pass results. Any future H4 daily-range exhaustion revisit needs a new versioned hypothesis and fresh SHA256 registration.
