# H4 GLD ETF Flow Reversal v1 Hypothesis

Hypothesis date: 2026-05-29
Hypothesis version: v1
Author / owner: maksoftwares / Codex
Mechanic family: GLD ETF participation/flow-stress reversal
Entry / decision timeframe: H4 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 72-288
Expected median hold hours: 6-24
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 50-350
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 40%-80%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.50R reversals after elevated GLD ETF participation. Reject if results require changing the volume percentile, z-score, return threshold, decision hours, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

Important audit note: this is a result-informed v1. It exists because `h4_gld_etf_flow_reversal_v0` produced the strongest independent PF lead so far but failed trade count, activity, and concentration gates. This v1 is not represented as a clean ex-ante v0 discovery. It is a separately registered attempt to test whether a broader, still-mechanical GLD-flow definition preserves the PF lead while clearing activity requirements.

## Mechanical Definition

`h4_gld_etf_flow_reversal_v1` tests whether elevated GLD ETF participation and a one-day GLD price shock mark a gold-flow stress event that can reverse during the next XAUUSD H4 session.

Data source:

- GLD ETF daily OHLCV proxy from Yahoo Finance chart API symbol `GLD`.
- This is a public non-primary ETF flow proxy, not COMEX order-flow, not broker fill data, and not live execution evidence.
- Every GLD feature is shifted by one observation before merging into XAUUSD H4 bars.

Signal rules:

1. Use only XAUUSD H4 decision bars ending at 08:00, 12:00, 16:00, or 20:00 UTC.
2. Compute GLD daily return, GLD volume percentile over 252 observations, GLD log-volume z-score over 126 observations, and GLD dollar-volume z-score over 126 observations.
3. A GLD flow-stress event requires:
   - shifted GLD volume percentile >= 0.75
   - max(shifted GLD log-volume z-score, shifted GLD dollar-volume z-score) >= 0.80
   - absolute shifted GLD one-day return >= 0.003
4. Long setup:
   - shifted GLD one-day return <= -0.003
   - current XAU H4 12-bar return <= -0.0025
   - current H4 candle closes above open
   - current H4 close location >= 0.58 of its own range
   - current H4 close is not more than 0.50 H4 ATR above H4 EMA40
5. Short setup:
   - shifted GLD one-day return >= 0.003
   - current XAU H4 12-bar return >= 0.0025
   - current H4 candle closes below open
   - current H4 close location <= 0.42 of its own range
   - current H4 close is not more than 0.50 H4 ATR below H4 EMA40
6. Entry is simulated at market from the signal bar close.
7. Stop is 1.15 x H4 ATR14 from entry.
8. Target is 1.50R.
9. Time stop is 6 H4 bars.
10. Maximum one signal per UTC day per direction.

## Expected Behavior

Expected trade count: moderate H4 frequency, likely 50-350 trades per 3-year cell.
Expected PF: at least 1.30 in 7 of 9 matrix cells if GLD participation stress contains a real XAU reversal mechanism.
Expected losing-month percentage: below 50%.
Expected worst month: no worse than -10R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

The v0 GLD-flow candidate showed that a public ETF participation proxy may identify a real XAU reversal state, but it sampled too few trades to be buildable. This v1 tests the broader version of the same economic idea: not only the most extreme GLD volume shocks, but elevated GLD participation with a directional GLD price shock. If the edge is real, it should remain visible after broader sampling and p95 cost. If it was a small-sample artifact, the broader sample should dilute quickly and fail.

## What Would Falsify It

Reject v1 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the data source cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v1 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
