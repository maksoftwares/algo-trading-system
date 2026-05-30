# H1 Policy Uncertainty Intraday Reversal v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: policy-uncertainty shock intraday reversal
Entry / decision timeframe: H1 completed-candle decision with M5 market-entry simulation
Expected median hold bars M5-equivalent: 48-144
Expected median hold hours: 4-12
Expected decisions per week: 0-8
Timeframe diversification qualifies: yes
Expected trade count per year: 60-450
Expected cost-adjusted PF: 1.05-1.55
Expected losing-month percentage: 35%-70%
Expected worst single month: -8R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Many 1R losses, occasional 1.45R reversals when policy-uncertainty shocks cause short-term XAU overreaction. Reject if results require changing shock thresholds, reversal confirmation, stop, target, or time stop after first-pass evidence.

## Status

Research-only candidate. Disabled until explicitly run through the research-candidate command path.

## Mechanical Definition

`h1_policy_uncertainty_intraday_reversal_v0` tests whether shifted US economic-policy-uncertainty shocks identify short-term XAU H1 overreaction/reversal opportunities.

Data source:

- FRED `USEPUINDXD`, the US Economic Policy Uncertainty Index daily observation.
- The policy series is shifted one daily observation before merging into XAUUSD H1 bars.

Signal rules:

1. Use only XAUUSD H1 decision bars ending at 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, or 20:00 UTC.
2. Compute shifted 3-business-day EPU mean.
3. Compute shifted 90-business-day EPU median.
4. Compute shifted `policy_uncertainty_ratio_3d_90d = 3d mean / 90d median`.
5. Compute shifted 10-business-day EPU change and its 252-business-day z-score.
6. Policy shock is active when shifted 3d/90d EPU ratio >= 1.45 or shifted 10d EPU-change z-score >= 1.00.
7. Policy relief is active when shifted 3d/90d EPU ratio <= 0.75 and shifted 10d EPU-change z-score <= -0.55.
8. Long setup:
   - policy shock is active
   - XAU H1 24-bar log return <= -0.004
   - XAU H1 8-bar log return >= -0.002
   - current H1 candle closes above open
   - current H1 close location >= 0.62
   - current H1 close <= EMA50 x 1.012
9. Short setup:
   - policy relief is active
   - XAU H1 24-bar log return >= +0.004
   - XAU H1 8-bar log return <= +0.002
   - current H1 candle closes below open
   - current H1 close location <= 0.38
   - current H1 close >= EMA50 x 0.988
10. Entry is simulated at market from the signal bar close.
11. Stop is 0.95 x H1 ATR14 from entry.
12. Target is 1.45R.
13. Time stop is 18 H1 bars.
14. Maximum one signal per UTC day per direction.

## Expected Behavior

Expected trade count: moderate H1 frequency, likely 60-450 trades per 3-year cell.
Expected PF: at least 1.30 in 7 of 9 matrix cells if policy-uncertainty shock overreaction contains tradable XAU reversal information.
Expected losing-month percentage: below 60%.
Expected worst month: no worse than -12R on fixed-notional reporting.
Expected zero-trade months: no more than 3 consecutive months.

## Why This Hypothesis Should Exist

The rejected H4 policy-uncertainty safe-haven candidate tested continuation when policy stress aligned with XAU trend. This v0 tests the opposite microstructure reading: policy-uncertainty spikes may produce noisy intraday XAU overreaction, and a completed H1 reversal candle after a short-term extreme may capture mean reversion without relying on support/resistance retests. This is not a level-and-pullback strategy.

## What Would Falsify It

Reject v0 without tuning if any of the following occur:

- fewer than 7 of 9 matrix cells reach PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gates fail
- cost-sensitivity gate fails
- max zero-trade months exceeds 3
- the USEPUINDXD source cannot cover the matrix windows
- the edge appears only in one broker window

Do not tune v0 thresholds after first-pass results. Any revisit must use a new versioned hypothesis and fresh SHA256 registration.
