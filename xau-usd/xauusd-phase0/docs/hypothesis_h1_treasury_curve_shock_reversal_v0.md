# H1 Treasury Curve Shock Reversal v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: Treasury-rate and curve shock intraday reversal
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 48-144
Expected median hold hours: 4-12
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 60-500
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses, occasional 1.45R reversals when rate/curve shocks and XAU intraday overreaction diverge. Reject if results require changing shock thresholds, reversal confirmation, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

## Mechanical Definition

`h1_treasury_curve_shock_reversal_v0` tests whether shifted US Treasury rate/curve shocks identify short-term XAU H1 overreaction/reversal opportunities.

Data source:

- FRED `DGS2`, the 2-year Treasury yield.
- FRED `DGS10`, the 10-year Treasury yield.
- FRED `T10Y2Y`, the 10-year minus 2-year Treasury spread.
- All series are shifted one daily observation before merging into XAUUSD H1 bars.

Signal rules:

1. Use only XAUUSD H1 decision bars ending at 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, or 21:00 UTC.
2. Compute shifted 10-business-day changes in DGS2, DGS10, and T10Y2Y.
3. Compute shifted 252-business-day z-score of the DGS2 10-day change.
4. Easing/steepening shock is active when shifted DGS2 change <= -0.12, shifted DGS10 change <= -0.07, and shifted T10Y2Y change >= +0.03, or when shifted DGS2 change z-score <= -0.75.
5. Tightening/flattening shock is active when shifted DGS2 change >= +0.12, shifted DGS10 change >= +0.07, and shifted T10Y2Y change <= -0.03, or when shifted DGS2 change z-score >= +0.75.
6. Long setup:
   - easing/steepening shock is active
   - XAU H1 24-bar log return <= -0.004
   - XAU H1 8-bar log return >= -0.002
   - current H1 candle closes above open
   - current H1 close location >= 0.60
   - current H1 close <= EMA50 x 1.015
7. Short setup:
   - tightening/flattening shock is active
   - XAU H1 24-bar log return >= +0.004
   - XAU H1 8-bar log return <= +0.002
   - current H1 candle closes below open
   - current H1 close location <= 0.40
   - current H1 close >= EMA50 x 0.985
8. Entry is simulated at market from the signal bar close.
9. Stop is 1.00 x H1 ATR14 from entry.
10. Target is 1.45R.
11. Time stop is 18 H1 bars.
12. Maximum one signal per UTC day per direction.

## Expected Behavior

Expected trade count: moderate H1 frequency, likely 60-500 trades per 3-year cell.
Expected PF: at least 1.30 in 7 of 9 matrix cells if Treasury-rate and curve shocks contain tradable XAU reversal information.
Expected losing-month percentage: below 60%.
Expected worst month: no worse than -12R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

The rejected H4 Treasury-curve candidate tested slow momentum alignment with rate stress. This v0 tests a different mechanism: rate/curve shocks may produce short-term XAU overreaction or lag, and a completed H1 reversal candle after that shock may capture mean reversion without relying on support/resistance retests. This is not a level-and-pullback strategy.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the DGS2/DGS10/T10Y2Y sources cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
