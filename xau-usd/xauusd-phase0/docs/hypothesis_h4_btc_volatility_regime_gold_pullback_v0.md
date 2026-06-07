# H4 BTC Volatility Regime Gold Pullback v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 20-100
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 30%-70%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: H4 trend-pullback continuation trades in BTC high-volatility regimes, with wider stops and lower turnover than M5 retest systems.

## Mechanical Definition

This candidate tests a new BTC lane: shifted BTC daily volatility regime as a risk-context gate for XAUUSD H4 trend pullback continuation. It is not a BTC return-pressure reversal, not a BTC volume-climax reversal, and not a local level/retest breakout. It uses BTC volatility state rather than BTC direction as the external input.

Data source:

- XAUUSD H4 broker bars from the existing 9-cell matrix.
- Existing public Yahoo BTC-USD daily OHLCV proxy at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- BTC daily features are shifted by one completed daily observation before H4 alignment.

BTC volatility features:

1. Compute BTC 1-day log return.
2. Compute BTC 10-day realized volatility and 40-day realized volatility.
3. Compute `btc_vol_ratio_10_40 = realized_vol_10d / realized_vol_40d`.
4. Compute 252-day percentile ranks for BTC 10-day volatility and BTC absolute 1-day return.
5. BTC volatility regime is active when:
   - `btc_vol_ratio_10_40 >= 1.12`
   - `btc_vol_percentile252 >= 0.62`
   - `btc_abs_return_percentile252 >= 0.48`

H4 execution:

1. Compute H4 ATR14, EMA40, EMA120, 3-bar return, and 12-bar return.
2. Long setup:
   - BTC volatility regime active
   - H4 close above EMA40 and EMA40 above EMA120
   - H4 12-bar return >= +0.40%
   - H4 3-bar return between -1.20% and +0.15%
   - current candle closes bullish
   - low trades no more than `1.40 x ATR14` above EMA40
   - close location >= 0.52
   - close is between `-0.20 x ATR14` and `2.80 x ATR14` from EMA40
3. Short setup mirrors the long setup below EMA40/EMA120.
4. At most one signal per two-day bucket and direction.
5. Trade plan uses market entry, `1.60 x H4 ATR14` stop, `1.55R` target, and a planned 10-H4-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 400 points.
- Measured median spread: 50 points = 0.1250R.
- Measured P95 spread: 75 points = 0.1875R.
- Structural status: PASS.

## Expected Behavior

The candidate expects gold trend-pullback continuation to behave differently when crypto volatility is elevated, because BTC volatility can proxy cross-asset speculative stress and risk-budget repricing without relying on BTC direction. If the mechanism exists, the BTC volatility gate should improve persistence versus pure XAU H4 pullback systems while maintaining enough activity to pass the 40-trade cell floor.

## Why This Hypothesis Should Exist

Prior BTC branches mostly tested BTC directional pressure, crash/rally continuation, volume climax, or XAU breakout behavior during BTC volatility regimes. `h4_btc_volatility_regime_gold_breakout_v0` solved activity but only reached 3/9 PF cells, all Pepperstone-only. This candidate tests a different H4 execution: continuation after pullback inside the BTC volatility regime rather than immediate expansion breakout.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
