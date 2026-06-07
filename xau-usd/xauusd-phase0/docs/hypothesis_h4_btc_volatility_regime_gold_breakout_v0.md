# H4 BTC Volatility Regime Gold Breakout v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 20-120
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 35%-75%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Sparse H4 continuation bursts with moderate right-tail if BTC volatility repricing marks cross-asset risk expansion.

## Mechanical Definition

This candidate tests whether BTC volatility regime transitions, independent of BTC return direction, can identify H4 XAU expansion conditions.

Data source:

- BTC-USD daily OHLCV proxy from Yahoo Finance file at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC features are shifted by one completed daily observation before merging into H4 XAU bars.

BTC regime features:

1. Compute daily BTC log return.
2. Compute 10-day realized BTC volatility and 40-day realized BTC volatility.
3. Compute `btc_vol_ratio_10_40 = btc_realized_vol_10d / btc_realized_vol_40d`.
4. Compute 252-day percentile ranks for 10-day realized volatility and absolute 1-day BTC return.
5. BTC volatility regime is active when:
   - `btc_vol_ratio_10_40 >= 1.18`
   - `btc_vol_percentile252 >= 0.68`
   - `btc_abs_return_percentile252 >= 0.55`

XAU H4 execution features:

1. ATR14, EMA40, 3-bar return, and 12-bar return are computed on H4 XAU bars.
2. Long setup:
   - BTC volatility regime active
   - H4 close is above open and above EMA40
   - `h4_return_3 >= 0.0018`
   - `h4_return_12 >= -0.0120`
   - close location in candle range is at least `0.62`
   - candle range is at least `0.70 x ATR14`
   - EMA40 distance is between `-0.35` and `3.25` ATR
3. Short setup:
   - BTC volatility regime active
   - H4 close is below open and below EMA40
   - `h4_return_3 <= -0.0018`
   - `h4_return_12 <= 0.0120`
   - close location in candle range is at most `0.38`
   - candle range is at least `0.70 x ATR14`
   - EMA40 distance is between `-3.25` and `0.35` ATR
4. At most one signal per two-day UTC bucket per direction.
5. Trade plan uses market entry, `1.50 x H4 ATR14` stop, `1.65R` target, and planned 8-H4-bar time stop.

## Expected Behavior

The candidate expects BTC volatility expansion to be a cross-asset risk-regime marker rather than a directional BTC lead. If the mechanism exists, XAU should trend through local H4 expansion bars more cleanly when BTC volatility is repricing abruptly.

## Why This Hypothesis Should Exist

Prior BTC candidates used BTC return pressure as the main signal. They either produced sparse pockets or diluted into negative cross-broker expectancy. This v0 tests a different BTC information channel: volatility transition instead of return direction. XAU direction is determined locally by H4 expansion state.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
