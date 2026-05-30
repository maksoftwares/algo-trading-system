# H1 GVZ Realized-Volatility Spread Follow-Through v0 Hypothesis

Hypothesis date: 2026-05-30
Hypothesis version: v0
Author / owner: maksoftwares / Codex
Mechanic family: H1 options-implied volatility premium follow-through
Entry / decision timeframe: H1 completed-candle decision with M5 execution sequencing
Expected median hold bars M5-equivalent: 24-216
Expected median hold hours: 2-18
Expected decisions per week: 0-10 during high GVZ premium regimes
Timeframe diversification qualifies: yes
Expected trade count per year: 30-500
Expected cost-adjusted PF: 1.05-1.65
Expected losing-month percentage: 35%-75%
Expected worst single month: -8R to -35R
Expected max consecutive zero months: 6
Expected R-multiple distribution: sparse H1 options-volatility premium shocks with stop losses near -1R and clustered 1.50R wins when GVZ premium and local XAU direction align.
Hypothesis SHA256: pending registration
Expert: `h1_gvz_realized_vol_spread_followthrough_v0`
Status at registration: research candidate only; not approved for EA coding, paper trading, or live execution.

## Mechanical Definition

This candidate uses shifted public FRED `GVZCLS` gold implied-volatility observations plus H1 XAU realized volatility.

The GVZ observations are shifted by one completed daily observation before merging into XAU H1 decisions.

Volatility-premium features:

```text
h1_realized_vol_ann_pct = 72-hour H1 realized volatility annualized to percent
gvz_return_5d = log(GVZCLS / GVZCLS 5 observations ago)
gvz_percentile252 = rolling percentile rank of GVZCLS over 252 observations
gvz_realized_spread = GVZCLS - h1_realized_vol_ann_pct
gvz_realized_spread_z252 = rolling z-score of gvz_realized_spread over 252 H1-aligned observations
```

Volatility-premium regime:

```text
gvz_percentile252 >= 0.65
AND gvz_return_5d >= +0.03
AND (gvz_realized_spread >= 4.0 OR gvz_realized_spread_z252 >= 0.45)
```

Long setup:

```text
volatility-premium regime is active
XAU H1 24-bar return >= +0.0040
XAU H1 8-bar return >= -0.0010
current H1 candle closes bullish
current H1 close location >= 0.58
close >= EMA40 - 0.75 x H1 ATR(14)
```

Short setup:

```text
volatility-premium regime is active
XAU H1 24-bar return <= -0.0040
XAU H1 8-bar return <= +0.0010
current H1 candle closes bearish
current H1 close location <= 0.42
close <= EMA40 + 0.75 x H1 ATR(14)
```

Execution:

```text
Entry: market at signal bar close
Stop: 1.05 x H1 ATR(14)
Target: 1.50R
Time stop: 18 H1 bars
Duplicate control: maximum one signal per UTC day per direction
Decision hours: 06:00, 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00 UTC
```

## Expected Behavior

The strategy should capture XAU continuation when options-implied gold volatility is rising faster than local realized volatility and spot has already started trending in one direction.

## Why This Hypothesis Should Exist

The existing H1 GVZ-realized-volatility spread reversal candidate rejected the opposite hypothesis: that XAU fades after a high GVZ premium. This candidate tests the paired follow-through mechanism without changing the data class after seeing the reversal result. It is distinct from retest, round-number, session, GLD-flow, futures-volume, FX-rotation, rates/credit shocks, financial-conditions shocks, and M5 path-structure candidates.

## What Would Falsify It

Reject v0 if fewer than 7/9 matrix cells reach PF >= 1.30, if trade count is insufficient, if the effect is broker-specific, if concentration or activity gates fail, if cost sensitivity fails, or if GVZ observations are not shifted before XAU H1 decisions. Do not tune v0 after results are known.
