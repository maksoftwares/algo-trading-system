# H1 Financial Conditions Shock Reversal v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: financial-conditions shock intraday reversal
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 48-144
Expected median hold hours: 4-12
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 50-450
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses, occasional 1.45R reversals when financial-conditions shocks and XAU intraday overreaction diverge. Reject if results require changing shock thresholds, reversal confirmation, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

## Mechanical Definition

`h1_financial_conditions_shock_reversal_v0` tests whether shifted US financial-conditions shocks identify short-term XAU H1 overreaction/reversal opportunities.

Data source:

- FRED `NFCI`, Chicago Fed National Financial Conditions Index.
- FRED `ANFCI`, Chicago Fed Adjusted National Financial Conditions Index.
- Both weekly series are shifted one observation before merging into XAUUSD H1 bars.

Signal rules:

1. Use only XAUUSD H1 decision bars ending at 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, or 21:00 UTC.
2. Compute shifted 4-week change in NFCI and ANFCI.
3. Compute shifted 156-week rolling percentile of NFCI.
4. Financial-tightening shock is active when shifted NFCI change >= +0.12, shifted ANFCI change >= +0.10, or shifted NFCI percentile >= 0.65.
5. Financial-easing shock is active when shifted NFCI change <= -0.12, shifted ANFCI change <= -0.10, or shifted NFCI percentile <= 0.35.
6. Long setup:
   - financial-tightening shock is active
   - XAU H1 24-bar log return <= -0.004
   - XAU H1 8-bar log return >= -0.002
   - current H1 candle closes above open
   - current H1 close location >= 0.60
   - current H1 close <= EMA50 x 1.015
7. Short setup:
   - financial-easing shock is active
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

Expected trade count: moderate H1 frequency, likely 50-450 trades per 3-year cell.
Expected PF: at least 1.30 in 7 of 9 matrix cells if broad financial-conditions shocks contain tradable XAU reversal information.
Expected losing-month percentage: below 60%.
Expected worst month: no worse than -12R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

The rejected H4 financial-conditions candidate tested slower stress reversal. This v0 tests a different timing mechanism: weekly financial-condition tightening/easing shocks may cause short-term XAU intraday overreaction, and a completed H1 reversal candle may capture that reversal without relying on support/resistance retests. This is not a level-and-pullback strategy.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the NFCI/ANFCI sources cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
