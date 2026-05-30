# H4 GLD ETF Flow Reversal v2 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v2
Author / owner: maksoftwares / Codex
Mechanic family: GLD ETF participation/flow-stress reversal
Entry / decision timeframe: H4 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 72-288
Expected median hold hours: 6-24
Expected decisions per week: 0-6
Timeframe diversification qualifies: yes
Expected trade count per year: 40-180
Expected cost-adjusted PF: 1.10-1.55
Expected losing-month percentage: 35%-75%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses and time stops, with occasional 1.50R reversals after elevated GLD ETF participation. Reject if results require changing the volume percentile, z-score, return threshold, decision hours, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

Important audit note: this is a result-informed v2. It exists because `h4_gld_etf_flow_reversal_v0` produced the strongest independent PF lead so far but failed trade count, activity, and concentration, while `h4_gld_etf_flow_reversal_v1` broadened both threshold and timing and diluted PF to 0/9 cells. This v2 is a narrower mechanical timing test: preserve the original v0 stress definition and add only the 08:00 UTC H4 decision slot.

## Mechanical Definition

`h4_gld_etf_flow_reversal_v2` tests whether unusually high GLD ETF participation and a one-day GLD price shock mark a gold-flow stress event that can reverse during the next XAUUSD H4 session, including the earlier 08:00 UTC decision bar.

Data source:

- GLD ETF daily OHLCV proxy from Yahoo Finance chart API symbol `GLD`.
- This is a public non-primary ETF flow proxy, not COMEX order-flow, not broker fill data, and not live execution evidence.
- Every GLD feature is shifted by one observation before merging into XAUUSD H4 bars.

Signal rules:

1. Use only XAUUSD H4 decision bars ending at 08:00, 12:00, 16:00, or 20:00 UTC.
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

Expected trade count: moderate H4 frequency, likely 40-180 trades per 3-year cell if the 08:00 timing slot captures enough additional stress reversals.
Expected PF: at least 1.30 in 7 of 9 matrix cells if the original GLD participation-stress edge is real and was partially missed by timing.
Expected losing-month percentage: below 55%.
Expected worst month: no worse than -10R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

The v0 result suggests the GLD participation-stress state may carry real XAU reversal information, but the sample was just below activity requirements. The v1 result shows that weakening stress thresholds destroys the edge. This v2 tests the narrower explanation: the stress definition may be right, but the allowed H4 decision schedule was too late in some sessions.

## What Would Falsify It

Reject v2 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the data source cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v2 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
