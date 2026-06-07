# H4 BTC Volume Climax Gold Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 20-110
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 35%-75%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: Sparse H4 reversal bursts with moderate right-tail if BTC volume climax marks crypto-liquidity rotation into or out of XAU.

## Mechanical Definition

This candidate tests whether shifted BTC daily volume climax can mark H4 XAU reversal windows. It is not a retune of the prior BTC return-pressure or BTC realized-volatility candidates: BTC volume intensity is the primary gate, while XAU H4 exhaustion/rejection decides direction.

Data source:

- BTC-USD daily OHLCV proxy from Yahoo Finance file at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC features are shifted by one completed daily observation before merging into H4 XAU bars.
- XAUUSD H4 broker bars from the existing 9-cell matrix.

BTC features:

1. Compute daily BTC 1-day, 3-day, and 10-day log returns.
2. Compute 126-day z-score of log BTC volume.
3. Compute 252-day percentile rank of log BTC volume.
4. Compute 5-day average BTC volume divided by 40-day average BTC volume.
5. BTC volume climax is active when:
   - `btc_volume_z126 >= 0.95`
   - `btc_volume_percentile252 >= 0.78`
   - `btc_volume_ratio_5_40 >= 1.12`

XAU H4 execution features:

1. ATR14, EMA50, 3-bar return, and 6-bar return are computed on H4 XAU bars.
2. Long setup:
   - BTC volume climax active
   - BTC 3-day return <= -3.0%
   - BTC 1-day return <= +1.2%
   - XAU 6-bar return <= -0.50%
   - XAU 3-bar return >= -1.20%
   - H4 candle closes bullish
   - close location in candle range is at least `0.58`
   - close is no more than `2.50 x ATR14` below EMA50
3. Short setup:
   - BTC volume climax active
   - BTC 3-day return >= +3.0%
   - BTC 1-day return >= -1.2%
   - XAU 6-bar return >= +0.50%
   - XAU 3-bar return <= +1.20%
   - H4 candle closes bearish
   - close location in candle range is at most `0.42`
   - close is no more than `2.50 x ATR14` above EMA50
4. At most one signal per ISO week and direction.
5. Trade plan uses market entry, `1.45 x H4 ATR14` stop, `1.55R` target, and planned 7-H4-bar time stop.

## Expected Behavior

The candidate expects BTC volume climax to identify crypto-liquidity stress/euphoria days where gold can reverse after local H4 exhaustion. If the mechanism exists, XAU should show better reversal expectancy after high BTC participation than after BTC return shocks alone.

## Why This Hypothesis Should Exist

Prior BTC candidates found either sparse return-pressure pockets or a broker-fragmented BTC volatility-regime pocket. This candidate tests a separate BTC information channel available in the current public proxy data: participation intensity. It should exist only if BTC volume carries rotation information not captured by raw BTC return magnitude or realized-volatility expansion.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
