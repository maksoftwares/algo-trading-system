# H1 GVZ/VIX Vol-Premium Reversal v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: Gold implied-volatility premium stress reversal
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 36-216
Expected median hold hours: 3-18
Expected decisions per week: 0-10
Timeframe diversification qualifies: yes
Expected trade count per year: 80-450
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 40%-80%
Expected worst single month: -10R to -24R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.50R reversals when gold-specific implied-volatility stress exhausts a local XAU move. Reject if results require changing GVZ/VIX thresholds, H1 exhaustion rules, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

Important audit note: this is not a breakout, retest, round-number, or support/resistance strategy. It tests whether gold-specific implied-volatility stress, measured as GVZ rising faster than VIX, marks local XAU exhaustion when an H1 reversal candle appears.

## Mechanical Definition

`h1_gvz_vix_vol_premium_reversal_v0` tests whether an expansion in gold implied volatility versus broad equity implied volatility identifies gold-specific panic that can mean-revert after a completed H1 reversal candle.

Data source:

- FRED GVZCLS gold-volatility index observations.
- FRED VIXCLS equity-volatility index observations.
- XAUUSD H1 and M5 broker bars.
- All GVZ/VIX features are shifted one observation before they are merged into XAUUSD H1 bars.

Feature rules:

1. Compute daily log GVZ/VIX ratio.
2. Compute 252-observation z-score of the GVZ/VIX ratio.
3. Compute five-observation GVZ return and VIX return.
4. Compute five-observation GVZ/VIX ratio change and its 126-observation z-score.
5. Gold-volatility-premium state is true only if:
   - GVZ/VIX ratio z-score >= 0.45
   - GVZ five-day return is greater than VIX five-day return
   - GVZ/VIX ratio five-day change >= 0.030 or its z-score >= 0.45

Signal rules:

1. Use completed XAUUSD H1 bars only.
2. Long setup:
   - gold-volatility-premium state is true
   - H1 six-bar log return <= -0.0025
   - H1 candle closes bullish
   - H1 close location within the candle range >= 0.58
   - H1 close is not more than 0.60 x H1 ATR14 above EMA40
3. Short setup:
   - gold-volatility-premium state is true
   - H1 six-bar log return >= 0.0025
   - H1 candle closes bearish
   - H1 close location within the candle range <= 0.42
   - H1 close is not more than 0.60 x H1 ATR14 below EMA40
4. Entry is simulated at market from the H1 signal close.
5. Stop is 1.10 x H1 ATR14 from entry.
6. Target is 1.50R.
7. Time stop is 18 H1 bars.
8. Maximum one signal per UTC day per direction.

## Expected Behavior

Expected trade count: moderate H1 frequency, likely 80-450 trades per year if gold-specific volatility-premium states persist long enough to create local H1 exhaustion candles.
Expected PF: at least 1.30 in 7 of 9 matrix cells if the vol-premium stress state has independent reversal value.
Expected losing-month percentage: below 55%.
Expected worst month: no worse than -12R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

Prior GVZ-only and VIX-only candidates treated gold implied volatility and broad equity-risk volatility separately. This candidate tests a relative mechanism: GVZ expanding faster than VIX may indicate gold-specific stress rather than generic risk-off behavior. If that stress exhausts a short-term XAU move, the first completed H1 reversal candle may offer a measurable mean-reversion point without relying on retests of price levels.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the data source cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
