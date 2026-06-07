# H4 GLD GVZ Vol Flow Reversal v0 Hypothesis

Hypothesis date: 2026-06-07
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Expected trade count per year: 20-120
Expected cost-adjusted PF: 1.00-1.50
Expected losing-month percentage: 25%-70%
Expected worst single month: -6R to -18R
Expected max consecutive zero months: 3
Expected R-multiple distribution: H4 XAU rejection trades gated by simultaneous GLD ETF flow stress and GVZ/VIX gold-volatility premium.

## Mechanical Definition

This candidate combines two independent public proxy data classes that each produced incomplete but nonzero clues: GLD ETF flow stress and GVZ/VIX gold-volatility premium. It is not a retest, round-number, breakout, BTC, or XAU-only OHLC system. It is also not a threshold edit of either single-source rejected candidate; both external states must be active before H4 XAU rejection can trigger.

Data source:

- XAUUSD H4 broker bars from the existing 9-cell matrix.
- Public Yahoo GLD daily OHLCV proxy at `data/reference/etf/gld_daily_yahoo_2015_2025.csv`.
- Public FRED GVZCLS gold implied-volatility observations.
- Public FRED VIXCLS equity implied-volatility observations.
- All daily external features are shifted by one completed observation before H4 alignment.

External state:

1. GLD flow stress is active when:
   - GLD daily volume percentile >= `0.70`
   - max(GLD volume z-score, GLD dollar-volume z-score) >= `0.45`
   - absolute GLD 1-day return >= `0.25%`
2. Gold volatility premium is active when:
   - GVZ/VIX log-ratio z-score >= `0.25`
   - GVZ 5-day return exceeds VIX 5-day return
   - GVZ/VIX ratio 5-day change >= `0.015` or its z-score >= `0.25`

H4 execution:

1. Compute H4 ATR14, EMA40, 6-bar return, and 12-bar return.
2. Long setup:
   - GLD flow stress and gold volatility premium are both active
   - shifted GLD return is negative
   - H4 6-bar return <= `-0.30%`
   - H4 12-bar return >= `-5.50%`
   - completed H4 candle closes bullish
   - close location >= `0.58`
   - close is not more than `0.90 x ATR14` above EMA40
3. Short setup mirrors the long setup after positive GLD flow stress and H4 upside overextension.
4. At most one signal per ISO week and direction.
5. Trade plan uses market entry, `1.35 x H4 ATR14` stop, `1.55R` target, and a planned 8-H4-bar time stop.

Measured-cost structural precheck:

- Expected median stop distance: 400 points.
- Measured median spread: 50 points = 0.1250R.
- Measured P95 spread: 75 points = 0.1875R.
- Structural status: PASS expected before real matrix.

## Expected Behavior

The candidate expects H4 XAU rejection to transfer better when both participation and options-volatility pressure are elevated. GLD flow stress alone was too sparse or diluted when broadened; GVZ/VIX premium alone was more persistent but below the PF threshold. The combined state should reduce false reversals while keeping enough activity if the two proxies describe the same gold-specific stress regime.

## Why This Hypothesis Should Exist

`h4_gld_etf_flow_reversal_v0` reached PF >= 1.30 in 9/9 cells but failed sample size and concentration. Broader GLD-flow variants diluted. `h4_gvz_vix_vol_premium_reversal_v0` had 9/9 positive-PnL cells but failed PF coverage, zero-month, and concentration gates. This candidate tests whether requiring both abnormal GLD participation and gold-specific volatility premium creates a cleaner H4 reversal subset than either proxy alone.

## What Would Falsify It

Reject v0 without tuning if any of the following fail:

- fewer than 7 of 9 matrix cells reach cost-adjusted PF >= 1.30
- any matrix cell has fewer than 40 trades
- max consecutive zero-trade months exceeds 3
- cross-broker persistence is absent
- concentration gate fails
- real matrix results depend on a single broker, a single cost case, or a small number of outlier trades

Do not tune v0 thresholds after first-pass results.
