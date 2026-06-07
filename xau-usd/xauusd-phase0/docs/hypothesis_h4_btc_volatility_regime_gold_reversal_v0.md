# H4 BTC Volatility Regime Gold Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 30-150
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 30%-70%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: H4 gold exhaustion-reversal trades during shifted high BTC realized-volatility regimes.

## Mechanical Definition

This candidate tests high BTC volatility as a cross-asset regime filter with XAUUSD H4 exhaustion reversal timing. It is not a BTC direction-pressure strategy and it is not a continuation version of the prior BTC volatility-regime breakout or pullback candidates.

Data source:

- XAUUSD H4 broker bars from the existing 9-cell matrix.
- Existing public Yahoo BTC-USD daily OHLCV proxy at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC daily features are shifted by one completed daily observation before H4 alignment.

BTC volatility-regime features:

1. Compute BTC 1-day log return.
2. Compute BTC 10-day and 40-day realized volatility.
3. Compute `btc_vol_ratio_10_40 = realized_vol_10d / realized_vol_40d`.
4. Compute 252-day percentile ranks for BTC 10-day volatility and BTC absolute 1-day return.
5. High BTC volatility regime is active when:
   - `btc_vol_ratio_10_40 >= 1.12`
   - `btc_vol_percentile252 >= 0.62`
   - `btc_abs_return_percentile252 >= 0.48`

H4 execution:

1. Compute H4 ATR14, EMA40, 3-bar return, and 6-bar return.
2. Long setup:
   - high BTC volatility regime is active
   - H4 6-bar return <= `-0.40%`
   - H4 3-bar return >= `-1.20%`
   - completed H4 candle closes bullish
   - close location >= `0.58`
   - close is no farther than `-2.75 x ATR14` below EMA40
3. Short setup mirrors the long setup after upside overextension.
4. At most one signal per ISO week and direction.
5. Trade plan uses market entry, `1.45 x H4 ATR14` stop, `1.55R` target, and a planned 8-H4-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 400 points.
- Measured median spread: 50 points = 0.1250R.
- Measured P95 spread: 75 points = 0.1875R.
- Structural status: PASS expected before real matrix.

## Expected Behavior

The candidate expects XAU H4 exhaustion reversals to behave better when BTC volatility is already elevated, because speculative risk appetite is unstable and cross-asset reversals may be cleaner than continuation breakouts.

## Why This Hypothesis Should Exist

`h4_btc_volatility_regime_gold_breakout_v0` solved activity but produced only Pepperstone PF pockets. `h4_btc_volatility_regime_gold_pullback_v0` became too sparse, and `h4_btc_volatility_compression_gold_expansion_v0` was negative across all cells. This version tests whether the missing piece is reversal timing during high BTC volatility rather than continuation timing.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
