# H4 Daily Range Extension Continuation v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex

Expected trade count per year: 30-180
Expected cost-adjusted PF: 0.95-1.45
Expected losing-month percentage: 35%-80%
Expected worst single month: -6R to -22R
Expected max consecutive zero months: 4
Expected R-multiple distribution: moderate-frequency H4 continuation losses near -1R with 1.40R wins after an already-expanded UTC day continues.

## Mechanical Definition

Expert: `h4_daily_range_extension_continuation_v0`

This is a disabled Phase 0R research candidate. It tests the paired interpretation of rejected `h4_daily_range_extension_reversal_v0`: instead of fading an already-extended UTC day, it follows the extension only when a completed H4 candle closes in the extension direction.

Data source:

- XAUUSD H4, D1, and M5 bars from the existing broker matrix windows.
- No external, future, or live MT5 data is used.

Feature construction:

1. Calculate H4 ATR(14), H4 range, H4 body ratio, H4 close location, current UTC day open/high/low so far, and the prior 20-day median D1 range.
2. Evaluate only completed H4 bars ending at 08:00, 12:00, 16:00, or 20:00 UTC.
3. Upside continuation setup:
   - Current UTC day high minus day open is at least 0.85 times prior 20-day median D1 range.
   - The H4 bar touches the current day high within 0.10 ATR.
   - The H4 candle is bullish and closes in the upper 35% of its range.
   - H4 range is at least 0.60 ATR and body ratio is at least 0.22.
   - Signal LONG.
4. Downside continuation setup:
   - Current UTC day open minus day low is at least 0.85 times prior 20-day median D1 range.
   - The H4 bar touches the current day low within 0.10 ATR.
   - The H4 candle is bearish and closes in the lower 35% of its range.
   - H4 range is at least 0.60 ATR and body ratio is at least 0.22.
   - Signal SHORT.
5. Use at most one signal per UTC day.
6. Entry is next simulated market entry after the completed H4 signal bar.
7. Stop is 0.25 H4 ATR beyond the signal candle low/high.
8. Target is 1.40R.
9. Planned time stop is 5 completed H4 bars.

Implementation mapping:

- Strategy: `src/phase0/strategies/h4_daily_range_extension_continuation_v0.py`
- Synthetic fixture: `src/phase0/synthetic.py::_h4_daily_range_extension_continuation_context`
- Test: `tests/test_h4_daily_range_extension_continuation_v0.py`

## Expected Behavior

This candidate should be active enough to clear the 40-trade cell floor if day-extension continuation is a real behavior. It should fail if extended-day continuation is just a late-entry chase that reverses after costs.

## Why This Hypothesis Should Exist

The rejected daily-range extension reversal v0 tested fading extended days and failed with 0/9 PF cells despite enough trades. This candidate asks the opposite, pre-registered question: does continuation after the same day-extension condition behave better than reversal?

It remains independent from level-and-pullback candidates because it does not use round numbers, session highs/lows as retest levels, swing levels, breakout acceptance, or pullback retests. The trigger is current UTC day range consumption plus H4 continuation candle quality.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- max consecutive zero-trade months exceeds 4
- cost sensitivity fails under p95 measured spread
- any broker family is materially negative across cost models
- any future edit changes thresholds after seeing first-pass matrix results

This candidate must not proceed to deciles, multisymbol, Gate 9, Phase 1, Phase 2, demo, paper execution, or live execution unless the matrix first-pass gate is satisfied.
