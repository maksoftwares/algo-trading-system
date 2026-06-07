# H1 BTC GVZ Dual Vol Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 40-220
Expected cost-adjusted PF: 1.00-1.45
Expected losing-month percentage: 30%-70%
Expected worst single month: -8R to -22R
Expected max consecutive zero months: 3
Expected R-multiple distribution: H1 gold rejection trades during combined BTC volatility stress and gold-volatility premium.

## Mechanical Definition

This candidate is a fresh H1 execution test of the combined BTC volatility stress plus GVZ/VIX gold-volatility premium clue. It is not a tune of `h4_btc_gvz_dual_vol_reversal_v0`: the H4 version remains rejected as a sparse PF lead. This version tests whether moving only the execution layer to H1 can solve activity while keeping both external volatility regimes mandatory.

Data sources:

- XAUUSD H1 broker bars from the existing 9-cell matrix.
- Public Yahoo BTC-USD daily OHLCV proxy at `data/reference/crypto/btc_usd_daily_yahoo_2015_2025.csv`.
- Public FRED GVZCLS observations.
- Public FRED VIXCLS observations.
- BTC, GVZ, and VIX daily features are shifted by one completed daily observation before H1 alignment.

BTC volatility-stress state:

1. Compute BTC 1-day log returns.
2. Compute 10-day and 40-day BTC realized volatility.
3. Compute `btc_vol_ratio_10_40 = realized_vol_10d / realized_vol_40d`.
4. Compute 252-day percentile ranks for BTC 10-day volatility and absolute 1-day return.
5. BTC volatility stress is active when:
   - `btc_vol_ratio_10_40 >= 1.04`
   - `btc_vol_percentile252 >= 0.52`
   - `btc_abs_return_percentile252 >= 0.42`

Gold-volatility premium state:

1. Compute GVZ and VIX 5-day returns.
2. Compute GVZ/VIX ratio, 252-day z-score, 5-day ratio change, and 126-day change z-score.
3. Gold-volatility premium is active when:
   - `gvz_vix_ratio_z252 >= 0.30`
   - `gvz_return_5d > vix_return_5d`
   - `gvz_vix_ratio_change_5d >= 0.018` or `gvz_vix_ratio_change_z126 >= 0.30`

H1 execution:

1. Compute H1 ATR14, EMA40, 6-bar return, and 12-bar return.
2. Evaluate only at UTC hours 7, 10, 13, 16, and 19.
3. Long setup:
   - BTC volatility stress is active
   - gold-volatility premium is active
   - H1 6-bar return <= `-0.20%`
   - H1 12-bar return >= `-4.00%`
   - completed H1 candle closes bullish
   - close location >= `0.56`
   - close is no farther than `1.20 x ATR14` above EMA40
4. Short setup mirrors the long setup after upside overextension.
5. At most one signal per calendar day and direction.
6. Trade plan uses market entry, `1.35 x H1 ATR14` stop, `1.45R` target, and a planned 18-H1-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 300 points.
- Measured median spread: 50 points = 0.1667R.
- Measured P95 spread: 75 points = 0.2500R.
- Structural status: PASS expected before real matrix.

## Expected Behavior

The H4 BTC+GVZ candidate found a PF pocket but failed activity. This H1 version expects the same external state to offer more reversal opportunities while the wider H1 stop keeps cost sensitivity tolerable.

## Why This Hypothesis Should Exist

`h4_btc_gvz_dual_vol_reversal_v0` produced 6/9 PF cells above 1.30 and 8/9 non-negative cells, but only 10-21 trades per cell. This candidate tests a clearly pre-registered activity-broadening execution layer rather than changing the H4 result after the fact.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
