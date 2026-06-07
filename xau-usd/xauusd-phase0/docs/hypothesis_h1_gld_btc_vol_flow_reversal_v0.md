# H1 GLD BTC Vol Flow Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 25-180
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 35%-80%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Intraday H1 reversal attempts during completed GLD flow stress and BTC volatility expansion regimes.

## Mechanical Definition

This candidate tests whether the sparse H4 GLD/BTC flow-regime clue can become active enough when executed on H1 rather than H4. It remains independent from level/retest mechanics and uses two shifted daily data classes.

Data sources:

- GLD daily OHLCV proxy from `data/reference/etf/gld_daily_yahoo_2015_2025.csv`.
- BTC-USD daily OHLCV proxy from `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- Both daily feature sets are shifted by one completed observation before merging into H1 XAU bars.

Signal rules:

1. Use only H1 bars closing at UTC hours `8`, `12`, `16`, or `20`.
2. GLD flow stress is active when:
   - `gld_volume_percentile252 >= 0.80`
   - max of `gld_volume_z126` and `gld_dollar_volume_z126` is at least `0.85`
   - `abs(gld_return_1d) >= 0.0030`
3. BTC volatility regime is active when:
   - `btc_vol_ratio_10_40 >= 1.08`
   - `btc_vol_percentile252 >= 0.60`
   - `btc_abs_return_percentile252 >= 0.48`
4. Long setup:
   - GLD return is negative: `gld_return_1d <= -0.0030`
   - H1 XAU 12-bar return is weak: `h1_return_12 <= -0.0012`
   - short-term return is stabilizing: `h1_return_6 >= h1_return_12`
   - H1 24-bar return is not a crash: `h1_return_24 >= -0.0180`
   - current H1 candle closes bullish with close location at least `0.58`
   - close is no more than `1.00 ATR` above EMA50
5. Short setup:
   - GLD return is positive: `gld_return_1d >= 0.0030`
   - H1 XAU 12-bar return is strong: `h1_return_12 >= 0.0012`
   - short-term return is cooling: `h1_return_6 <= h1_return_12`
   - H1 24-bar return is not a blowoff: `h1_return_24 <= 0.0180`
   - current H1 candle closes bearish with close location at most `0.42`
   - close is no more than `1.00 ATR` below EMA50
6. At most one signal per UTC day per direction.
7. Trade plan uses market entry, `1.35 x H1 ATR14` stop, `1.45R` target, and planned 10-H1-bar time stop.

## Expected Behavior

The H4 combined version produced a sparse PF clue in Pepperstone and Dukascopy but failed the trade-count gate. This H1 version expects the same completed daily stress regime to produce more intraday reversal opportunities while preserving enough selectivity to avoid diluting edge.

## Why This Hypothesis Should Exist

The strongest independent clues are GLD flow stress and BTC volatility expansion. The H4 combination was too sparse, not useless. This candidate tests a different execution layer rather than tuning the same H4 thresholds.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- results are explained by one broker, one cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
