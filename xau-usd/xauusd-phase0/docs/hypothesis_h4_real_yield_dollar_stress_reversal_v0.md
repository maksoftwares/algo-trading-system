# H4 Real-Yield Dollar Stress Reversal v0 Hypothesis

Hypothesis date: 2026-06-01
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H4 macro-stress overreaction reversal
Entry / decision timeframe: H4 completed-candle decisions with M5 execution bars in the Phase 0 simulator
Expected median hold bars M5-equivalent: 96-384
Expected median hold hours: 16-64
Expected decisions per week: 0-4
Timeframe diversification qualifies: yes
Expected trade count per year: 45-180
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 42%-58%
Expected worst single month: -8R to -14R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses, time stops, and occasional 1.65R winners after H4 macro-stress overreaction candles. Reject if results require changing macro thresholds, H4 return windows, rejection-candle rules, stop multiplier, target, or weekly signal cap after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

This candidate is deliberately higher-timeframe and macro-pressure based. It is not a breakout-retest, round-level, GLD-flow, options-skew, or same-family level-pullback hypothesis.

## Mechanical Definition

The strategy uses shifted daily FRED `DFII10` 10-year real-yield data and shifted daily FRED `DTWEXBGS` broad-dollar data. It never uses same-day macro observations before the H4 decision bar because the macro feature frame is shifted by one observation before merge-as-of alignment.

For each completed H4 candle:

1. Compute H4 ATR(14), EMA(40), 6-bar log return, 12-bar log return, and 24-bar log return.
2. Compute 20-business-day real-yield change, 20-business-day broad-dollar log return, and 252-business-day z-scores for both macro changes.
3. Allow at most one signal per ISO week and direction.
4. Long setup:
   - `real_yield_change_20d >= 0.16`
   - `dollar_return_20d >= 0.0050`
   - `max(real_yield_change_z252, dollar_return_z252) >= 0.50`
   - H4 12-bar XAU return `<= -0.0050`
   - H4 24-bar XAU return `>= -0.0450`
   - H4 6-bar XAU return `<= 0.0010`
   - candle closes above open
   - close location inside candle range `>= 0.60`
   - close is no more than 2.50 ATR below EMA40
5. Short setup:
   - `real_yield_change_20d <= -0.16`
   - `dollar_return_20d <= -0.0050`
   - `min(real_yield_change_z252, dollar_return_z252) <= -0.50`
   - H4 12-bar XAU return `>= 0.0050`
   - H4 24-bar XAU return `<= 0.0450`
   - H4 6-bar XAU return `>= -0.0010`
   - candle closes below open
   - close location inside candle range `<= 0.40`
   - close is no more than 2.50 ATR above EMA40
6. Enter at market on the next available M5 execution path.
7. Stop is 1.25 H4 ATR from estimated entry.
8. Target is 1.65R.
9. Planned time stop is 8 completed H4 bars / 384 M5 bars.

## Why This Hypothesis Should Exist

Gold often faces mechanical pressure when real yields and the broad dollar rise together. This hypothesis does not bet on that pressure continuing indefinitely; it tests whether a mature joint pressure shock creates temporary H4 overshoot once spot gold has already sold off and then prints a completed rejection candle. The short side tests the symmetric case: macro conditions that are normally supportive for gold may become temporarily overextended when price has already rallied and rejects higher prices.

This is intentionally different from the approved breakout/retest family:

- no level break is required
- no retest is required
- no M5/M15 structure signal is used
- the causal input is macro pressure plus H4 overreaction, not support/resistance continuation

## Expected Behavior

Expected trade count: moderate H4 frequency, likely 45-180 trades per year if real-yield and dollar stress cycles create enough H4 overreaction candles across brokers.
Expected PF: at least 1.30 in 7 of 9 matrix cells if macro-pressure overreaction reversal has persistent XAU value after costs.
Expected losing-month percentage: below 58%.
Expected worst month: no worse than -14R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells have PF >= 1.30
- any cell has fewer than 40 trades
- max drawdown exceeds 30%
- total return is below -25%
- largest single-trade contribution exceeds 10%
- top-five trade contribution exceeds 40%
- max zero-trade months exceeds 3
- P95/best PF ratio is below 0.50
- decile PF persistence fails
- multisymbol consistency fails or the XAU-specific defense is weak
- manual adversarial logic-gap rate exceeds 25%

## Code Mapping

- Strategy implementation: `src/phase0/strategies/h4_real_yield_dollar_stress_reversal_v0.py`
- Macro data loader: `src/phase0/macro_real_yield_data.py`
- Synthetic smoke context: `src/phase0/synthetic.py::_h4_real_yield_dollar_stress_reversal_context`
- Test: `tests/test_h4_real_yield_dollar_stress_reversal_v0.py`
