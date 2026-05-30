# H1 GVZ/VIX Volatility Premium Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 gold-specific implied-volatility premium follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-216
Expected median hold hours: 2-18
Expected decisions per week: 0-10 during gold-volatility premium regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 30-600
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-75%
Expected worst single month: -8R to -35R
Expected max consecutive zero months: 6
Expected R-multiple distribution: sparse H1 gold-specific volatility-premium shocks with stop losses near -1R and clustered 1.50R wins when GVZ/VIX premium expansion and local XAU direction align.
Hypothesis SHA256: pending registration
Expert: `h1_gvz_vix_vol_premium_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses shifted public FRED gold and equity implied-volatility series:

- `GVZCLS`: Cboe Gold ETF Volatility Index.
- `VIXCLS`: Cboe S&P 500 Volatility Index.

The GVZ and VIX observations are shifted by one completed daily observation before merging into XAU H1 decisions.

Gold-volatility premium features:

```text
gvz_return_5d = log(GVZCLS / GVZCLS 5 observations ago)
vix_return_5d = log(VIXCLS / VIXCLS 5 observations ago)
gvz_vix_ratio = log(GVZCLS / VIXCLS)
gvz_vix_ratio_z252 = rolling z-score of gvz_vix_ratio over 252 observations
gvz_vix_ratio_change_5d = gvz_vix_ratio - gvz_vix_ratio 5 observations ago
gvz_vix_ratio_change_z126 = rolling z-score of gvz_vix_ratio_change_5d over 126 observations
```

Gold-volatility premium regime:

```text
gvz_vix_ratio_z252 >= +0.45
AND gvz_return_5d > vix_return_5d
AND (gvz_vix_ratio_change_5d >= +0.030 OR gvz_vix_ratio_change_z126 >= +0.45)
```

Long setup:

```text
gold-volatility premium regime is active
XAU H1 6-bar return >= +0.0025
current H1 candle closes bullish
current H1 close location >= 0.58
close >= EMA40 - 0.60 x H1 ATR(14)
```

Short setup:

```text
gold-volatility premium regime is active
XAU H1 6-bar return <= -0.0025
current H1 candle closes bearish
current H1 close location <= 0.42
close <= EMA40 + 0.60 x H1 ATR(14)
```

Execution:

```text
Entry: market at signal bar close
Stop: 1.10 x H1 ATR(14)
Target: 1.50R
Time stop: 18 H1 bars
Duplicate control: maximum one signal per UTC day per direction
```

## Expected Behavior

The strategy should capture XAU continuation when gold-specific implied volatility is expanding relative to broad equity implied volatility and spot has already started moving in the same direction.

## Why This Hypothesis Should Exist

The existing H1 GVZ/VIX volatility-premium reversal candidate rejected the opposite hypothesis: that gold-specific vol premium should fade after a local H1 reversal candle. This candidate tests the paired follow-through mechanism without changing the data class after seeing the reversal result. It is distinct from retest, round-number, session, GLD-flow, futures-volume, FX-rotation, rates/credit shocks, financial-conditions shocks, and M5 path-structure candidates.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if GVZ/VIX observations are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
