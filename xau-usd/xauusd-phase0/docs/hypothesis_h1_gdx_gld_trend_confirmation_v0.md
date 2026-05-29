# H1 GDX/GLD Trend Confirmation v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: GDX/GLD miner-confirmed H1 trend continuation
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
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.50R continuations when miner relative strength confirms XAU trend direction. Reject if results require changing relative-strength threshold, z-score, percentile, decision hours, EMA rules, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

## Mechanical Definition

`h1_gdx_gld_trend_confirmation_v0` tests whether gold miners can confirm XAU trend continuation. It is not a retest, round-number, swing-level, or breakout-retest strategy.

Data source:

- GLD ETF daily OHLCV proxy from Yahoo Finance chart API symbol `GLD`.
- GDX gold-miners ETF daily OHLCV proxy from Yahoo Finance chart API symbol `GDX`.
- This is a public non-primary ETF proxy, not COMEX order-flow, not broker fill data, and not live execution evidence.
- Every ETF feature is shifted by one observation before merging into XAUUSD H1 bars.

Signal rules:

1. Use only XAUUSD H1 decision bars ending at 08:00, 12:00, 16:00, or 20:00 UTC.
2. Compute shifted 5-day GLD return, shifted 5-day GDX return, and `miner_relative_return_5d = gdx_return_5d - gld_return_5d`.
3. Compute 126-day z-score and 252-day absolute percentile of the shifted miner relative return.
4. Long setup:
   - shifted 5-day miner relative return >= 0.012
   - shifted miner relative z-score >= 0.45
   - shifted absolute relative-return percentile >= 0.55
   - XAU H1 close is above EMA50
   - EMA21 is above or equal to EMA50
   - the H1 bar touches or pulls back near EMA21
   - 6-bar H1 return is non-negative
   - H1 candle closes bullish with close location >= 0.55
5. Short setup:
   - shifted 5-day miner relative return <= -0.012
   - shifted miner relative z-score <= -0.45
   - shifted absolute relative-return percentile >= 0.55
   - XAU H1 close is below EMA50
   - EMA21 is below or equal to EMA50
   - the H1 bar touches or pulls back near EMA21
   - 6-bar H1 return is non-positive
   - H1 candle closes bearish with close location <= 0.45
6. Entry is simulated at market from the H1 signal close.
7. Stop is 1.15 x H1 ATR14 from entry.
8. Target is 1.50R.
9. Time stop is 12 H1 bars.
10. Maximum one signal per UTC day per direction.

## Expected Behavior

Expected trade count: moderate H1 frequency, likely 80-500 trades per year if GDX/GLD confirmation is frequent enough.
Expected PF: at least 1.30 in 7 of 9 matrix cells if miner relative strength is a real trend-confirmation state for XAU.
Expected losing-month percentage: below 50%.
Expected worst month: no worse than -10R on fixed-notional reporting.
Expected zero-trade months: no more than 2 consecutive months.

## Why This Hypothesis Should Exist

The project needs a candidate that does not depend on XAU level retests. Gold miners are a related but distinct market: they embed gold sensitivity, equity-risk appetite, producer economics, and miner-specific positioning. If miners outperform GLD while XAU is already trending upward, the gold move may have cross-market confirmation. If miners underperform GLD while XAU trends downward, downside continuation may have confirmation. The H1 pullback rule prevents the candidate from buying or selling every ETF state and forces an XAU timing event.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- the data source cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
