# H4 BTC Whipsaw Gold Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 30-180
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 30%-70%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: H4 gold rejection trades during shifted BTC path-inefficient volatility regimes.

## Mechanical Definition

This candidate tests whether unstable, path-inefficient BTC regimes identify better XAUUSD H4 reversal windows. It is not a BTC directional pressure strategy, a BTC crash/rally continuation strategy, a BTC volume-climax strategy, or a threshold edit of the rejected BTC volatility-regime breakout/pullback/reversal candidates.

Data source:

- XAUUSD H4 broker bars from the existing 9-cell matrix.
- Existing public Yahoo BTC-USD daily OHLCV proxy at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC daily features are shifted by one completed daily observation before H4 alignment.

BTC whipsaw-regime features:

1. Compute BTC 1-day and 20-day log returns.
2. Compute 20-day path efficiency as `abs(20-day return) / rolling_sum(abs(1-day returns), 20)`.
3. Compute BTC 10-day and 40-day realized volatility.
4. Compute `btc_vol_ratio_10_40 = realized_vol_10d / realized_vol_40d`.
5. Compute 252-day percentile ranks for BTC 10-day volatility and BTC absolute 1-day return.
6. BTC whipsaw regime is active when:
   - `btc_path_efficiency_20d <= 0.42`
   - `btc_vol_ratio_10_40 >= 1.04`
   - `btc_vol_percentile252 >= 0.55`
   - `btc_abs_return_percentile252 >= 0.45`
   - `abs(btc_return_20d) <= 0.22`

H4 execution:

1. Compute H4 ATR14, EMA40, 3-bar return, 6-bar return, and 12-bar return.
2. Long setup:
   - BTC whipsaw regime is active
   - H4 6-bar return <= `-0.30%`
   - H4 12-bar return >= `-6.00%`
   - H4 3-bar return >= `-1.40%`
   - completed H4 candle closes bullish
   - close location >= `0.56`
   - close is no farther than `-3.10 x ATR14` below EMA40
3. Short setup mirrors the long setup after upside overextension.
4. At most one signal per three-day bucket and direction.
5. Trade plan uses market entry, `1.40 x H4 ATR14` stop, `1.55R` target, and a planned 8-H4-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 400 points.
- Measured median spread: 50 points = 0.1250R.
- Measured P95 spread: 75 points = 0.1875R.
- Structural status: PASS expected before real matrix.

## Expected Behavior

The candidate expects XAU H4 rejection trades to behave better when BTC has recently moved a lot but gone nowhere. That state may indicate unstable speculative positioning without requiring BTC to be in a clean directional crash or rally.

## Why This Hypothesis Should Exist

Earlier BTC attempts either found sparse stress pockets or enough activity with weak cross-broker PF. This version tests a different BTC state variable: path inefficiency under elevated realized volatility. It is designed to increase activity without directly broadening the rejected strict BTC stress signal.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
