# H1 BTC Risk Pressure Gold Follow-Through v2 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v2
Author / owner: maksoftwares / Codex

Expected trade count per year: 55-280
Expected cost-adjusted PF: 1.05-1.50
Expected losing-month percentage: 30%-78%
Expected worst single month: -7R to -20R
Expected max consecutive zero months: 4
Expected R-multiple distribution: Asymmetric continuation behavior with stronger follow-through on the stressed side.

## Mechanical Definition

This candidate tests whether BTC stress transitions produce a cleaner continuation signal in XAU when momentum/price structure is permissive but not over-constrained.

Data source:

- BTC-USD daily OHLCV proxy from Yahoo Finance at
  `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC features are merged into H1 bars with one-bar daily lag.

Signal construction:

1. Use only H1 bars at UTC hour `8`, `12`, `16`, or `20`.
2. Merge BTC 5-day returns, 20-day returns, 5-day z-score, 252-day percentile rank, and 126-day volume z-score.
3. BTC stress is active when all are true:
   - `abs(btc_return_5d) >= 0.070`
   - `abs(btc_return_z126) >= 0.35`
   - `btc_abs_return_percentile252 >= 0.60`
   - `btc_volume_z126 >= 0.20`
4. Long setup:
   - BTC return negative (`btc_return_5d <= -0.070`)
   - H1 continuation remains gentle (`h1_return_12 <= 0.0028`, `h1_return_6 <= 0.0010`)
   - close is below EMA21
   - bar closes in lower half (`close_location <= 0.55`)
5. Short setup:
   - BTC return positive (`btc_return_5d >= +0.070`)
   - H1 continuation remains gentle (`h1_return_12 >= -0.0028`, `h1_return_6 >= -0.0010`)
   - close is above EMA21
   - bar closes in upper half (`close_location >= 0.45`)
6. One signal max per UTC day per direction.
7. Trade plan uses ATR-driven stop (`1.15 x ATR14`) with `1.5R` target and `9` H1 bar time stop.

## Expected Behavior

BTC drawdown clusters should increase long-side continuation bias in XAU while BTC upside shocks should produce cleaner short-side follow-through. The candidate expects signal activity to persist across multiple years and across broker cost curves, with edge concentrated in stress-window cells if the cross-asset spillover is real.

## Why This Hypothesis Should Exist

v1 produced no synthetic smoke due synthetic fixture alignment, and its long and short filters were too restrictive for this behavior family.

This version keeps the BTC stress entry logic but uses simpler continuation gates intended to preserve edge while avoiding signal starvation.

## What Would Falsify It

Reject v2 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- concentration gate fails
- max cost-adjusted consecutive zero-trade months exceeds 4
- concentration/activity checks fail
- data unavailable or incomplete hypothesis change after lock

Do not tune thresholds in v2 after the first-pass matrix.
