# H4 GLD ETF Flow Reversal v3 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v3
Author / owner: maksoftwares / Codex
Expected trade count per year: 55-190
Expected cost-adjusted PF: 1.05-1.45
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -16R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.50R reversals after elevated GLD ETF participation.

## Mechanical Definition

`h4_gld_etf_flow_reversal_v3` tests whether unusually high GLD ETF participation and a one-day GLD price shock still identify a gold-flow stress reversal, while adding additional intraday H4 decision slots to capture missed sessions.

Data source:

- GLD ETF daily OHLCV proxy from Yahoo Finance symbol `GLD`.
- This is a public non-primary ETF flow proxy, not COMEX order-flow, not broker fill data, and not live execution evidence.
- Every GLD feature is shifted by one observation before merging into XAUUSD H4 bars.

Signal rules:

1. Use only XAUUSD H4 decision bars ending at 00:00, 04:00, 08:00, 12:00, 16:00, or 20:00 UTC.
2. Compute GLD daily return, GLD volume percentile over 252 observations, GLD log-volume z-score over 126 observations, and GLD dollar-volume z-score over 126 observations.
3. A GLD flow-stress event requires:
   - shifted GLD volume percentile >= 0.85
   - max(shifted GLD log-volume z-score, shifted GLD dollar-volume z-score) >= 1.15
   - absolute shifted GLD one-day return >= 0.004
4. Long setup:
   - shifted GLD one-day return <= -0.004
   - current XAU H4 12-bar return <= -0.0035
   - current H4 candle closes above open
   - current H4 close location >= 0.58 of its own range
   - current H4 close is not more than 0.50 H4 ATR above H4 EMA40
5. Short setup:
   - shifted GLD one-day return >= 0.004
   - current XAU H4 12-bar return >= 0.0035
   - current H4 candle closes below open
   - current H4 close location <= 0.42 of its own range
   - current H4 close is not more than 0.50 H4 ATR below H4 EMA40
6. Entry is simulated at market from the signal bar close.
7. Stop is 1.15 x H4 ATR14 from entry.
8. Target is 1.50R.
9. Time stop is 6 H4 bars.
10. Maximum one signal per UTC day per direction.

## Expected Behavior

The broader decision schedule is expected to improve sample coverage and trade frequency while preserving the v0/v2 edge. If this hypothesis is valid, we expect:

- trade counts in most matrix cells to rise into the 40-180 range or higher,
- better cell-level pass distribution than v2 if timing was the limiting factor,
- no severe increase in concentration risk relative to v2.

## Why This Hypothesis Should Exist

`h4_gld_etf_flow_reversal_v2` improved the earlier direction timing but still did not meet all gates, with persistent sample/frequency concentration constraints. If those failures are truly due to missed local sessions rather than edge degradation, adding 00:00 and 04:00 decision slots should better match stress windows without changing core GLD stress definitions.

## What Would Falsify It

Reject without retuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the edge appears only in one broker window
- the data source cannot cover the matrix windows
- later tuning is required to recover edge after first-pass failure
