# H4 GLD BTC Vol Flow Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 12-80
Expected cost-adjusted PF: 1.00-1.55
Expected losing-month percentage: 30%-80%
Expected worst single month: -5R to -16R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Sparse H4 reversal bursts when GLD flow stress and BTC volatility expansion overlap.

## Mechanical Definition

This candidate combines the two strongest independent clues found so far: GLD ETF flow stress and BTC volatility-regime expansion. It is not a retest/level strategy and does not use BTC return direction as the trade direction.

Data sources:

- GLD daily OHLCV proxy from `data/reference/etf/gld_daily_yahoo_2015_2025.csv`.
- BTC-USD daily OHLCV proxy from `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- Both daily feature sets are shifted by one completed observation before merging into H4 XAU bars.

Signal rules:

1. Use only H4 bars closing at UTC hours `8`, `12`, `16`, or `20`.
2. GLD flow stress is active when:
   - `gld_volume_percentile252 >= 0.82`
   - max of `gld_volume_z126` and `gld_dollar_volume_z126` is at least `0.95`
   - `abs(gld_return_1d) >= 0.0035`
3. BTC volatility regime is active when:
   - `btc_vol_ratio_10_40 >= 1.10`
   - `btc_vol_percentile252 >= 0.62`
   - `btc_abs_return_percentile252 >= 0.50`
4. Long setup:
   - GLD return is negative: `gld_return_1d <= -0.0035`
   - H4 XAU 12-bar return is weak: `h4_return_12 <= -0.0025`
   - current H4 candle closes bullish with close location at least `0.56`
   - close is no more than `0.75 ATR` above EMA40
5. Short setup:
   - GLD return is positive: `gld_return_1d >= 0.0035`
   - H4 XAU 12-bar return is strong: `h4_return_12 >= 0.0025`
   - current H4 candle closes bearish with close location at most `0.44`
   - close is no more than `0.75 ATR` below EMA40
6. At most one signal per UTC day per direction.
7. Trade plan uses market entry, `1.25 x H4 ATR14` stop, `1.55R` target, and planned 8-H4-bar time stop.

## Expected Behavior

If the mechanism is real, GLD stress identifies gold-specific liquidation/flow pressure while BTC volatility confirms a wider cross-asset risk regime. The combination should reduce broker-fragmented single-source pockets and preserve only higher-quality H4 reversals.

## Why This Hypothesis Should Exist

GLD-flow v0 had the strongest independent PF lead but failed activity and concentration. Broader GLD-flow versions solved activity but became broker-fragmented. BTC volatility-regime v0 solved activity and produced a strong Pepperstone pocket but failed Capital.com and Dukascopy. Combining the two tests whether the overlap is more persistent than either clue alone.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- results are explained by one broker or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
