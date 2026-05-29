# H1 GC Momentum Pullback v0 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: Futures-proxy momentum with spot pullback continuation
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 24-144
Expected median hold hours: 2-12
Expected decisions per week: 0-15
Timeframe diversification qualifies: yes
Expected trade count per year: 120-900
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 40%-80%
Expected worst single month: -10R to -24R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.50R continuations when shifted GC futures momentum aligns with a completed XAU H1 pullback candle. Reject if results require changing GC return thresholds, H1 EMA pullback rules, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

Important audit note: this is not a breakout, retest, round-number, or support/resistance strategy. It tests whether daily GC futures-proxy momentum can define the directional state for H1 XAU pullback continuations. This uses the existing non-authoritative Yahoo `GC=F` continuous futures proxy, not primary CME order-flow data.

## Mechanical Definition

`h1_gc_momentum_pullback_v0` tests whether shifted GC futures-proxy momentum improves XAUUSD H1 pullback continuation timing.

Data source:

- Yahoo `GC=F` daily OHLCV proxy already stored as `data/reference/futures/gc_continuous_daily_yahoo_2015_2025.csv`.
- XAUUSD H1 and M5 broker bars.
- GC daily features are shifted one observation before being merged into XAUUSD H1 bars.

Feature rules:

1. Compute shifted GC 5-day log return.
2. Compute shifted GC 20-day log return.
3. Compute XAUUSD H1 EMA21, EMA50, ATR14, and 24-bar log return.

Signal rules:

1. Use completed XAUUSD H1 bars only.
2. Evaluate only H1 bars ending at 07:00, 11:00, 15:00, or 19:00 UTC.
3. Long setup:
   - shifted GC 5-day log return >= 0.0060
   - shifted GC 20-day log return >= 0.0120
   - XAU H1 close >= EMA50
   - XAU H1 EMA21 >= EMA50
   - XAU H1 24-bar return >= -0.0010
   - H1 bar touches or pulls back near EMA21 within 0.35 x ATR14
   - H1 candle closes bullish
   - H1 close location within candle range >= 0.55
4. Short setup:
   - shifted GC 5-day log return <= -0.0060
   - shifted GC 20-day log return <= -0.0120
   - XAU H1 close <= EMA50
   - XAU H1 EMA21 <= EMA50
   - XAU H1 24-bar return <= 0.0010
   - H1 bar touches or pulls back near EMA21 within 0.35 x ATR14
   - H1 candle closes bearish
   - H1 close location within candle range <= 0.45
5. Entry is simulated at market from the H1 signal close.
6. Stop is 1.15 x H1 ATR14 from entry.
7. Target is 1.50R.
8. Time stop is 12 H1 bars.
9. Maximum one signal per UTC day per direction.

## Expected Behavior

Expected trade count: moderate H1 frequency, likely 120-900 trades per year if GC trend states persist long enough for H1 XAU pullbacks.
Expected PF: at least 1.30 in 7 of 9 matrix cells if GC futures-proxy direction provides independent timing value.
Expected losing-month percentage: below 55%.
Expected worst month: no worse than -12R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

Prior GC volume and GC/XAU basis attempts tested stress and convergence. This candidate tests a different GC-proxy mechanism: directional futures momentum as a higher-level state, with XAU H1 pullbacks used only for timing. If futures-led gold trend pressure is persistent, H1 continuation after a pullback should show positive expectancy without using breakout/retest levels.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the GC proxy cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
