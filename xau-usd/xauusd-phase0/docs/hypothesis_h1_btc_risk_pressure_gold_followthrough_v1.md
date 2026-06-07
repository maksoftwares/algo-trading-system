# H1 BTC Risk Pressure Gold Follow-Through v1 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v1
Author / owner: maksoftwares / Codex
Expected trade count per year: 40-220
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 35%-80%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: More asymmetric than v0 with longer right-tail on one-way BTC-risk transitions.

## Mechanical Definition

This revision tests whether BTC pressure asymmetry should be traded as a directionally conditional continuation
without requiring both trend and inverse-momentum overlap from the previous v0 rules.

Data source:

- BTC-USD daily OHLCV proxy from Yahoo Finance file at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- Features are shifted by one completed daily observation before merging into H1 XAU bars.

Signal rules:

1. Use only H1 bars that close at UTC hour `8`, `12`, `16`, or `20`.
2. Merge BTC 5-bar returns, 20-bar returns, 5-bar percentile/z-score, and volume z-score.
3. BTC stress gate is active when all of:
   - `abs(btc_return_5d) >= 0.07`
   - `abs(btc_return_z126) >= 0.40`
   - `btc_abs_return_percentile252 >= 0.60`
   - `btc_volume_z126 >= 0.50`
4. Long setup:
   - BTC return is negative (`btc_return_5d <= -0.07`)
   - `h1_return_12 <= 0.0035` and `h1_return_6 <= 0.0015`
   - short-term H1 momentum is not stronger than 12-bar momentum: `h1_return_6 <= h1_return_12`
   - current H1 close is below EMA21 and EMA50
   - bar closes in lower half of its own range (`close_location <= 0.42`)
5. Short setup:
   - BTC return is positive (`btc_return_5d >= +0.07`)
   - `h1_return_12 >= -0.0035` and `h1_return_6 >= -0.0015`
   - short-term H1 momentum is not weaker than 12-bar momentum: `h1_return_6 >= h1_return_12`
   - current H1 close is above EMA21 and EMA50
   - bar closes in upper half of its own range (`close_location >= 0.58`)
6. One signal max per UTC day per direction.
7. Trade plan uses ATR-driven stop (`1.15 x ATR14`) with `1.5R` target and `9` H1 bar time stop.

## Expected Behavior

The candidate expects BTC shocks to produce stronger immediate directional spillover into XAU than the first-pass v0 definition.
If true, long trades should dominate during severe BTC drawdowns, short trades should dominate during BTC squeezes/rallies.
The strategy should produce persistent H1 opportunities while avoiding the exact trend-state conjunctions that may have diluted v0.

## Why This Hypothesis Should Exist

v0 generated negative edge despite broad event alignment, suggesting the original `trend + same-direction momentum`
filters were likely too rigid. This v1 tests a simpler asymmetric spillover rule:
BTC risk state as a leading regime switch plus only mild H1 continuation/reversion structure.

If this mechanism is real, it should improve cost-adjusted edge by separating sign-specific behavior while reducing noise from mixed states.

## What Would Falsify It

Reject v1 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gate fails
- max cost-adjusted consecutive zero-trade months exceeds 3
- max drawdown gates or concentration/activity checks fail
- data is unavailable or requires proxy changes during run

Do not tune v1 thresholds after first-pass results.
