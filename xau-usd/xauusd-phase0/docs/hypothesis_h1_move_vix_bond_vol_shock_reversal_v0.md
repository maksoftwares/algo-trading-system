# H1 MOVE/VIX Bond-Vol Shock Reversal v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: Bond-implied-volatility shock reversal
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
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.50R reversals when rates-volatility stress exhausts a local XAU move. Reject if results require changing MOVE/VIX thresholds, H1 reversal rules, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

Important audit note: this is not a breakout, retest, round-number, support/resistance, FX-rotation, commodity-rotation, GVZ-only, or GVZ/VIX strategy. It tests whether bond-market implied-volatility stress, measured as MOVE rising sharply versus VIX, marks local XAUUSD H1 exhaustion.

## Mechanical Definition

`h1_move_vix_bond_vol_shock_reversal_v0` tests whether a sharp MOVE expansion versus VIX identifies rates-market stress that can exhaust a short-term XAUUSD move once a completed H1 reversal candle appears.

Data source:

- Yahoo Finance `^MOVE` daily OHLC observations as a public non-primary bond-volatility proxy.
- FRED VIXCLS equity-volatility index observations.
- XAUUSD H1 and M5 broker bars.
- All MOVE/VIX features are shifted one observation before they are merged into XAUUSD H1 bars.

Feature rules:

1. Compute daily five-observation MOVE log return.
2. Compute daily five-observation VIX log return.
3. Compute daily log MOVE/VIX ratio.
4. Compute 252-observation z-score of the MOVE/VIX ratio.
5. Compute five-observation MOVE/VIX ratio change and its 126-observation z-score.
6. Bond-volatility-shock state is true only if:
   - MOVE five-day return >= 0.060
   - MOVE five-day return exceeds VIX five-day return by at least 0.015
   - MOVE/VIX ratio z-score >= 0.35
   - MOVE/VIX ratio five-day change >= 0.035 or its z-score >= 0.40

Signal rules:

1. Use completed XAUUSD H1 bars only.
2. Long setup:
   - bond-volatility-shock state is true
   - H1 six-bar log return <= -0.0025
   - H1 24-bar log return >= -0.0300
   - H1 candle closes bullish
   - H1 close location within the candle range >= 0.60
   - H1 close is not more than 0.70 x H1 ATR14 above EMA40
3. Short setup:
   - bond-volatility-shock state is true
   - H1 six-bar log return >= 0.0025
   - H1 24-bar log return <= 0.0300
   - H1 candle closes bearish
   - H1 close location within the candle range <= 0.40
   - H1 close is not more than 0.70 x H1 ATR14 below EMA40
4. Entry is simulated at market from the H1 signal close.
5. Stop is 1.10 x H1 ATR14 from entry.
6. Target is 1.50R.
7. Time stop is 18 H1 bars.
8. Maximum one signal per UTC day per direction.

## Expected Behavior

Expected trade count: moderate H1 frequency, likely 80-450 trades per year if MOVE/VIX stress states create enough local gold exhaustion candles.
Expected PF: at least 1.30 in 7 of 9 matrix cells if bond-volatility stress has independent reversal value for XAU.
Expected losing-month percentage: below 55%.
Expected worst month: no worse than -12R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

Gold often reacts to rates volatility through real-yield, duration, and liquidity channels. A sharp MOVE expansion versus VIX can indicate rates-market stress that is not merely broad equity-risk panic. If that rates shock forces short-term gold liquidation or overbuying, the first completed H1 reversal candle may identify exhaustion without using price-level retests or rejected FX/ETF rotation families.

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
