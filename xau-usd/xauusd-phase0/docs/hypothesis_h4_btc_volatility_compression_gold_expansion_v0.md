# H4 BTC Volatility Compression Gold Expansion v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 30-140
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 30%-70%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: H4 expansion-continuation trades after BTC volatility compression, with wider stops and lower turnover than M5 retest systems.

## Mechanical Definition

This candidate tests the opposite BTC regime from prior BTC volatility-expansion candidates. It uses shifted BTC daily low-volatility compression as a cross-asset quiet-risk context, then trades XAUUSD H4 expansion in the direction of its H4 trend. It is not a BTC direction-pressure strategy, not a BTC high-volatility breakout strategy, and not a local level/retest system.

Data source:

- XAUUSD H4 broker bars from the existing 9-cell matrix.
- Existing public Yahoo BTC-USD daily OHLCV proxy at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC daily features are shifted by one completed daily observation before H4 alignment.

BTC volatility compression features:

1. Compute BTC 1-day log return.
2. Compute BTC 10-day realized volatility and 40-day realized volatility.
3. Compute `btc_vol_ratio_10_40 = realized_vol_10d / realized_vol_40d`.
4. Compute 252-day percentile ranks for BTC 10-day volatility and BTC absolute 1-day return.
5. BTC compression regime is active when:
   - `btc_vol_ratio_10_40 <= 0.88`
   - `btc_vol_percentile252 <= 0.42`
   - `btc_abs_return_percentile252 <= 0.55`

H4 execution:

1. Compute H4 ATR14, EMA40, EMA120, 3-bar return, and 12-bar return.
2. Long setup:
   - BTC compression regime active
   - H4 close above EMA40 and EMA40 above EMA120
   - current candle closes bullish
   - H4 3-bar return >= +0.20%
   - H4 12-bar return >= +0.10%
   - H4 range is at least `0.70 x ATR14`
   - close location >= 0.62
   - close is between `-0.35 x ATR14` and `3.00 x ATR14` from EMA40
3. Short setup mirrors the long setup below EMA40/EMA120.
4. At most one signal per two-day bucket and direction.
5. Trade plan uses market entry, `1.55 x H4 ATR14` stop, `1.60R` target, and a planned 10-H4-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 400 points.
- Measured median spread: 50 points = 0.1250R.
- Measured P95 spread: 75 points = 0.1875R.
- Structural status: PASS.

## Expected Behavior

The candidate expects XAU H4 expansion to be cleaner when BTC is quiet rather than already volatile. If BTC volatility compression represents dormant speculative/risk-budget pressure, XAU trend expansion may have better follow-through and less whipsaw than during BTC high-volatility regimes.

## Why This Hypothesis Should Exist

`h4_btc_volatility_regime_gold_breakout_v0` tested high BTC volatility and solved activity but produced only Pepperstone PF pockets. `h4_btc_volatility_regime_gold_pullback_v0` tested high BTC volatility plus XAU pullback continuation and became too sparse. This candidate tests a different BTC state: low BTC volatility compression, not high volatility expansion, while keeping H4/wider-stop execution.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
