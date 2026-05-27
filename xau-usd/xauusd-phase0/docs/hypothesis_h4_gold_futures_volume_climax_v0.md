# H4 Gold Futures Volume Climax v0 Hypothesis

Hypothesis date: 2026-05-27
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: GC futures daily-volume climax reversal
Entry / decision timeframe: H4 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 96-384
Expected median hold hours: 8-32
Expected decisions per week: 0-6
Timeframe diversification qualifies: yes
Expected trade count per year: 40-250
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 40%-80%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.55R reversals after unusually high GC futures volume. Reject if results require changing the volume percentile, z-score, decision hours, prior-day return threshold, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

## Mechanical Definition

`h4_gold_futures_volume_climax_v0` tests whether unusually high COMEX/GC continuous futures daily volume marks a one-day liquidation or exhaustion event in XAUUSD that can reverse during the next H4 session.

Data source:

- GC continuous futures daily OHLCV proxy from Yahoo Finance chart API symbol `GC=F`.
- This is not primary CME order-flow data. Treat it as a non-authoritative daily futures-volume proxy.
- Every daily futures-volume feature is shifted by one observation before merging into H4 bars.

Signal rules:

1. Use only XAUUSD H4 decision bars ending at 08:00, 12:00, or 16:00 UTC.
2. Compute GC daily volume percentile over 252 observations and log-volume z-score over 126 observations.
3. A volume climax requires:
   - shifted GC volume percentile >= 0.82
   - shifted GC log-volume z-score >= 1.00
   - shifted prior XAU D1 range >= 1.10 x D1 ATR14
4. Long setup:
   - prior XAU D1 return <= -0.004
   - current H4 candle closes above open
   - current H4 close location >= 0.58 of its own range
   - current H4 close is not more than 0.75 H4 ATR above H4 EMA40
5. Short setup:
   - prior XAU D1 return >= 0.004
   - current H4 candle closes below open
   - current H4 close location <= 0.42 of its own range
   - current H4 close is not more than 0.75 H4 ATR below H4 EMA40
6. Entry is simulated at market from the signal bar close.
7. Stop is 1.20 x H4 ATR14 from entry.
8. Target is 1.55R.
9. Time stop is 8 H4 bars.
10. Maximum one signal per UTC day.

## Expected Behavior

Expected trade count: moderate H4 frequency, likely 40-250 trades per 3-year cell.
Expected PF: at least 1.30 in 7 of 9 matrix cells if the volume-climax exhaustion mechanism is real.
Expected losing-month percentage: below 45%.
Expected worst month: no worse than -8R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

Most rejected independent candidates used spot XAU price geometry, slow macro series, or broad risk proxies. This candidate introduces a separate data class: exchange-traded gold futures volume. If volume spikes capture forced liquidation, hedging pressure, or participation exhaustion, the next H4 session may contain a measurable mean-reversion impulse that does not depend on the breakout-retest family.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- the data source cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
