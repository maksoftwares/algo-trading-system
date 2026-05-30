# H1 VIX Term-Structure Inversion Followthrough v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: VIX/VXV equity-volatility term-structure followthrough
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 36-96
Expected median hold hours: 3-8
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 80-500
Expected cost-adjusted PF: 1.05-1.50
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -20R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses, occasional 1.5R trend-followthrough winners after VIX term-structure inversion or relief. Reject if results require changing term-structure thresholds, confirmation rules, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

## Mechanical Definition

`h1_vix_term_structure_inversion_followthrough_v0` tests whether shifted VIX/VXV term-structure stress identifies short-term XAU H1 continuation better than absolute VIX level alone.

Data source:

- FRED `VIXCLS`, the CBOE Volatility Index daily close.
- FRED `VXVCLS`, the CBOE 3-Month Volatility Index daily close.
- Both sources are shifted one daily observation before merging into XAUUSD H1 bars.

Signal rules:

1. Use only XAUUSD H1 decision bars ending at 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00, or 21:00 UTC.
2. Compute shifted `vix_vxv_ratio = VIXCLS / VXVCLS`.
3. Compute shifted 5-business-day ratio change and its 126-business-day z-score.
4. Inversion panic is active when:
   - shifted VIX/VXV ratio >= 1.02
   - and shifted 5-day ratio change >= 0.025 or shifted ratio-change z-score >= 0.65
5. Contango relief is active when:
   - shifted VIX/VXV ratio <= 0.92
   - and shifted 5-day ratio change <= -0.020 or shifted ratio-change z-score <= -0.65
6. Long setup:
   - inversion panic is active
   - XAU H1 24-bar log return >= +0.004
   - XAU H1 72-bar log return <= +0.055
   - current H1 close > EMA50
   - current H1 candle closes above open
   - current H1 close location >= 0.58
7. Short setup:
   - contango relief is active
   - XAU H1 24-bar log return <= -0.004
   - XAU H1 72-bar log return >= -0.055
   - current H1 close < EMA50
   - current H1 candle closes below open
   - current H1 close location <= 0.42
8. Entry is simulated at market from the signal bar close.
9. Stop is 1.05 x H1 ATR14 from entry.
10. Target is 1.50R.
11. Time stop is 12 H1 bars.
12. Maximum one signal per UTC day per direction.

## Expected Behavior

Expected trade count: moderate H1 frequency, likely 80-500 trades per 3-year cell.
Expected PF: at least 1.30 in 7 of 9 matrix cells if VIX term-structure inversion contains tradable XAU continuation information.
Expected losing-month percentage: below 60%.
Expected worst month: no worse than -12R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

The rejected VIX/VXV reversal lane found mild Pepperstone and Dukascopy pockets but failed because Capital.com was negative and the expression was not robust. This followthrough lane tests a distinct mechanism: if front-month equity volatility is stressed relative to three-month volatility and XAU is already trending with that stress, gold may continue for several hours as safe-haven demand persists. This is not a price-level or retest strategy.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the VXVCLS source cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
